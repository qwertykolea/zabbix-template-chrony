import os
import uuid

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

NS = uuid.UUID('c57a9150-5f21-4d1a-9669-7cfa856df931')

def get_uuid(key: str) -> str:
    return uuid.uuid5(NS, key).hex

def generate_yaml(active: bool = False) -> str:
    mode = "active" if active else "passive"
    tpl_name = "Chrony by Zabbix agent 2 active" if active else "Chrony by Zabbix agent 2"
    tpl_desc = (
        "Production-grade Chrony NTP client monitoring for Zabbix Agent 2 (Active checks).\\n"
        "Features zero external shell scripts, single CSV master item polling, and low-level discovery (LLD) of NTP sources."
        if active else
        "Production-grade Chrony NTP client monitoring for Zabbix Agent 2 (Passive checks).\\n"
        "Features zero external shell scripts, single CSV master item polling, and low-level discovery (LLD) of NTP sources."
    )
    master_item_type = "\n          type: ZABBIX_ACTIVE" if active else ""
    proc_item_type = "\n          type: ZABBIX_ACTIVE" if active else ""

    tpl_uuid = get_uuid(f"template:{mode}")
    group_uuid = get_uuid("group:Applications")

    # JS Code snippets with exact indentation
    js_tracking = """                  var p = value.trim().split(',');
                  if (p.length < 13) {
                      throw 'Expected at least 13 CSV fields from chronyc -c tracking, got ' + p.length;
                  }
                  var raw_leap = p.length >= 14 ? p[13].trim() : p[12].trim();
                  var leap_code = 0;
                  if (raw_leap === 'Normal' || raw_leap === '0') {
                      leap_code = 0;
                  } else if (raw_leap === 'Insert second' || raw_leap === '1') {
                      leap_code = 1;
                  } else if (raw_leap === 'Delete second' || raw_leap === '2') {
                      leap_code = 2;
                  } else {
                      leap_code = 3;
                  }
                  var update_interval = p.length >= 14 ? parseFloat(p[12]) : 0.0;
                  return JSON.stringify({
                      ref_id: p[0],
                      ref_ip: p[1],
                      stratum: parseInt(p[2]),
                      ref_time: p[3],
                      system_time_offset: parseFloat(p[4]),
                      last_offset: parseFloat(p[5]),
                      rms_offset: parseFloat(p[6]),
                      freq_ppm: parseFloat(p[7]),
                      residual_freq: parseFloat(p[8]),
                      skew_ppm: parseFloat(p[9]),
                      root_delay: parseFloat(p[10]),
                      root_dispersion: parseFloat(p[11]),
                      update_interval: update_interval,
                      leap_status: leap_code
                  });"""

    js_sources = """                  var lines = value.trim().split('\\n');
                  var obj = {};
                  for (var i = 0; i < lines.length; i++) {
                      var line = lines[i].trim();
                      if (!line) continue;
                      var p = line.split(',');
                      if (p.length >= 10) {
                          var name = p[2];
                          obj[name] = {
                              mode: p[0],
                              state: p[1],
                              stratum: parseInt(p[3]),
                              poll: parseInt(p[4]),
                              reach_octal: p[5],
                              reach_val: parseInt(p[5], 8),
                              last_rx: parseInt(p[6]),
                              offset: parseFloat(p[7]),
                              margin: parseFloat(p[8]),
                              delay: parseFloat(p[9])
                          };
                      }
                  }
                  return JSON.stringify(obj);"""

    js_discovery = """                  var data = JSON.parse(value);
                  var result = [];
                  for (var k in data) {
                      result.push({
                          "{#SOURCE_NAME}": k,
                          "{#SOURCE_MODE}": data[k].mode
                      });
                  }
                  return JSON.stringify(result);"""

    out = f"""zabbix_export:
  version: '7.0'
  template_groups:
    - uuid: {group_uuid}
      name: Templates/Applications
  templates:
    - uuid: {tpl_uuid}
      template: '{tpl_name}'
      name: '{tpl_name}'
      description: '{tpl_desc}'
      groups:
        - name: Templates/Applications
      items:
        - uuid: {get_uuid(f'{mode}:item:proc.num')}
          name: 'Chrony: Service process state'{proc_item_type}
          key: 'proc.num[chronyd]'
          delay: 1m
          history: 14d
          value_type: UNSIGNED
          description: 'Checks if chronyd daemon process is running.'
          tags:
            - tag: component
              value: system
          triggers:
            - uuid: {get_uuid(f'{mode}:trigger:proc_down')}
              expression: 'last(/{tpl_name}/proc.num[chronyd])=0'
              name: 'Chrony: Service process is not running'
              priority: HIGH
              description: 'The chronyd background daemon process is not running. Clock synchronization is stopped.'
              tags:
                - tag: scope
                  value: availability

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking')}
          name: 'Chrony: Tracking raw data'{master_item_type}
          key: chrony.tracking
          delay: 1m
          history: 1h
          trends: '0'
          value_type: TEXT
          description: 'Raw CSV output from command: chronyc -c tracking'
          tags:
            - tag: component
              value: raw

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.json')}
          name: 'Chrony: Tracking JSON'
          type: DEPENDENT
          key: chrony.tracking.json
          delay: '0'
          history: 1h
          trends: '0'
          value_type: TEXT
          description: 'Parsed JSON structure from chronyc -c tracking raw CSV.'
          master_item:
            key: chrony.tracking
          preprocessing:
            - type: JAVASCRIPT
              parameters:
                - |
{js_tracking}
          tags:
            - tag: component
              value: json

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.offset.system')}
          name: 'Chrony: System time offset'
          type: DEPENDENT
          key: chrony.tracking.offset.system
          delay: '0'
          history: 30d
          value_type: FLOAT
          units: s
          description: 'Current offset between local system clock and reference NTP source (in seconds).'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.system_time_offset'
          tags:
            - tag: component
              value: ntp
          triggers:
            - uuid: {get_uuid(f'{mode}:trigger:offset_warn')}
              expression: 'min(/{tpl_name}/chrony.tracking.offset.system,3m)>{{$CHRONY.OFFSET.WARN}} or max(/{tpl_name}/chrony.tracking.offset.system,3m)<-{{$CHRONY.OFFSET.WARN}}'
              name: 'Chrony: Clock offset is excessive (> {{$CHRONY.OFFSET.WARN}}s)'
              priority: WARNING
              description: 'System clock offset has exceeded {{$CHRONY.OFFSET.WARN}}s (100ms) for at least 3 minutes.'
              dependencies:
                - name: 'Chrony: Service process is not running'
                  expression: 'last(/{tpl_name}/proc.num[chronyd])=0'
              tags:
                - tag: scope
                  value: performance
            - uuid: {get_uuid(f'{mode}:trigger:offset_crit')}
              expression: 'last(/{tpl_name}/chrony.tracking.offset.system)>{{$CHRONY.OFFSET.CRIT}} or last(/{tpl_name}/chrony.tracking.offset.system)<-{{$CHRONY.OFFSET.CRIT}}'
              name: 'Chrony: Clock offset is critical (> {{$CHRONY.OFFSET.CRIT}}s)'
              priority: HIGH
              description: 'System clock offset has critically deviated beyond {{$CHRONY.OFFSET.CRIT}}s (500ms).'
              dependencies:
                - name: 'Chrony: Clock offset is excessive (> {{$CHRONY.OFFSET.WARN}}s)'
                  expression: 'min(/{tpl_name}/chrony.tracking.offset.system,3m)>{{$CHRONY.OFFSET.WARN}} or max(/{tpl_name}/chrony.tracking.offset.system,3m)<-{{$CHRONY.OFFSET.WARN}}'
                - name: 'Chrony: Service process is not running'
                  expression: 'last(/{tpl_name}/proc.num[chronyd])=0'
              tags:
                - tag: scope
                  value: availability

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.offset.rms')}
          name: 'Chrony: RMS offset'
          type: DEPENDENT
          key: chrony.tracking.offset.rms
          delay: '0'
          history: 30d
          value_type: FLOAT
          units: s
          description: 'Long-term root mean square (RMS) average of the clock offset.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.rms_offset'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.offset.last')}
          name: 'Chrony: Last offset'
          type: DEPENDENT
          key: chrony.tracking.offset.last
          delay: '0'
          history: 14d
          value_type: FLOAT
          units: s
          description: 'Estimated local clock offset during the last clock update measurement.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.last_offset'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.stratum')}
          name: 'Chrony: Stratum'
          type: DEPENDENT
          key: chrony.tracking.stratum
          delay: '0'
          history: 30d
          value_type: UNSIGNED
          description: 'NTP Stratum level of the current time source (1 = primary server, 2-15 = secondary, 0 or >=16 = unsynchronized).'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.stratum'
          tags:
            - tag: component
              value: ntp
          triggers:
            - uuid: {get_uuid(f'{mode}:trigger:stratum_invalid')}
              expression: 'last(/{tpl_name}/chrony.tracking.stratum)=0 or last(/{tpl_name}/chrony.tracking.stratum)>=16'
              name: 'Chrony: Stratum is invalid (0 or >= 16)'
              priority: HIGH
              description: 'Stratum indicates the host is completely unsynchronized or upstream sources are invalid.'
              dependencies:
                - name: 'Chrony: Service process is not running'
                  expression: 'last(/{tpl_name}/proc.num[chronyd])=0'
              tags:
                - tag: scope
                  value: availability

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.leap_status')}
          name: 'Chrony: Leap status'
          type: DEPENDENT
          key: chrony.tracking.leap_status
          delay: '0'
          history: 30d
          value_type: UNSIGNED
          description: 'Leap second and sync status: 0=Normal, 1=Insert second, 2=Delete second, 3=Not synchronised.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.leap_status'
          valuemap:
            name: 'Chrony Leap Status'
          tags:
            - tag: component
              value: ntp
          triggers:
            - uuid: {get_uuid(f'{mode}:trigger:not_synced')}
              expression: 'last(/{tpl_name}/chrony.tracking.leap_status)=3'
              name: 'Chrony: Host is not synchronised with NTP'
              priority: HIGH
              description: 'Leap status is 3 (Not synchronised). Chrony has lost connection to all upstream servers.'
              dependencies:
                - name: 'Chrony: Service process is not running'
                  expression: 'last(/{tpl_name}/proc.num[chronyd])=0'
              tags:
                - tag: scope
                  value: availability

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.root_delay')}
          name: 'Chrony: Root delay'
          type: DEPENDENT
          key: chrony.tracking.root_delay
          delay: '0'
          history: 14d
          value_type: FLOAT
          units: s
          description: 'Total network round-trip delay to the stratum-1 reference clock.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.root_delay'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.root_dispersion')}
          name: 'Chrony: Root dispersion'
          type: DEPENDENT
          key: chrony.tracking.root_dispersion
          delay: '0'
          history: 14d
          value_type: FLOAT
          units: s
          description: 'Maximum estimated error dispersion accumulated to the primary clock source.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.root_dispersion'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.freq_ppm')}
          name: 'Chrony: Frequency'
          type: DEPENDENT
          key: chrony.tracking.freq_ppm
          delay: '0'
          history: 14d
          value_type: FLOAT
          units: ppm
          description: 'Estimated frequency drift of the local system clock in parts per million (PPM).'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.freq_ppm'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.residual_freq')}
          name: 'Chrony: Residual frequency'
          type: DEPENDENT
          key: chrony.tracking.residual_freq
          delay: '0'
          history: 14d
          value_type: FLOAT
          units: ppm
          description: 'Residual frequency offset between the clock and reference source in PPM.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.residual_freq'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.skew_ppm')}
          name: 'Chrony: Skew'
          type: DEPENDENT
          key: chrony.tracking.skew_ppm
          delay: '0'
          history: 14d
          value_type: FLOAT
          units: ppm
          description: 'Estimated error bound on the local clock frequency in PPM.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.skew_ppm'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.update_interval')}
          name: 'Chrony: Update interval'
          type: DEPENDENT
          key: chrony.tracking.update_interval
          delay: '0'
          history: 14d
          value_type: FLOAT
          units: s
          description: 'Interval between clock updates in seconds.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.update_interval'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.tracking.ref_ip')}
          name: 'Chrony: Reference source IP'
          type: DEPENDENT
          key: chrony.tracking.ref_ip
          delay: '0'
          history: 14d
          trends: '0'
          value_type: CHAR
          description: 'IP address or identifier of the active reference time source.'
          master_item:
            key: chrony.tracking.json
          preprocessing:
            - type: JSONPATH
              parameters:
                - '$.ref_ip'
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.sources')}
          name: 'Chrony: Sources raw data'{master_item_type}
          key: chrony.sources
          delay: 1m
          history: 1h
          trends: '0'
          value_type: TEXT
          description: 'Raw CSV output from command: chronyc -c sources'
          tags:
            - tag: component
              value: raw

        - uuid: {get_uuid(f'{mode}:item:chrony.sources.json')}
          name: 'Chrony: Sources JSON'
          type: DEPENDENT
          key: chrony.sources.json
          delay: '0'
          history: 1h
          trends: '0'
          value_type: TEXT
          description: 'Parsed JSON dictionary from chronyc -c sources for discovery and summaries.'
          master_item:
            key: chrony.sources
          preprocessing:
            - type: JAVASCRIPT
              parameters:
                - |
{js_sources}
          tags:
            - tag: component
              value: json

        - uuid: {get_uuid(f'{mode}:item:chrony.sources.count')}
          name: 'Chrony: Configured sources count'
          type: DEPENDENT
          key: chrony.sources.count
          delay: '0'
          history: 14d
          value_type: UNSIGNED
          description: 'Total number of configured NTP sources discovered in chrony.'
          master_item:
            key: chrony.sources.json
          preprocessing:
            - type: JAVASCRIPT
              parameters:
                - |
                  var o = JSON.parse(value);
                  return Object.keys(o).length;
          tags:
            - tag: component
              value: ntp

        - uuid: {get_uuid(f'{mode}:item:chrony.sources.synced_count')}
          name: 'Chrony: Synchronized sources count'
          type: DEPENDENT
          key: chrony.sources.synced_count
          delay: '0'
          history: 14d
          value_type: UNSIGNED
          description: 'Number of active NTP sources in synchronized (* or +) state.'
          master_item:
            key: chrony.sources.json
          preprocessing:
            - type: JAVASCRIPT
              parameters:
                - |
                  var o = JSON.parse(value);
                  var c = 0;
                  for (var k in o) {{
                      if (o[k].state === '*' || o[k].state === '+') c++;
                  }}
                  return c;
          tags:
            - tag: component
              value: ntp
          triggers:
            - uuid: {get_uuid(f'{mode}:trigger:sources_min')}
              expression: 'last(/{tpl_name}/chrony.sources.synced_count)<{{$CHRONY.SOURCES.MIN.WARN}}'
              name: 'Chrony: Low number of synchronized NTP sources (< {{$CHRONY.SOURCES.MIN.WARN}})'
              priority: WARNING
              status: DISABLED
              description: 'Optional trigger (disabled by default). Alert fires when synchronized sources drop below the threshold.'
              dependencies:
                - name: 'Chrony: Service process is not running'
                  expression: 'last(/{tpl_name}/proc.num[chronyd])=0'
              tags:
                - tag: scope
                  value: notice

      discovery_rules:
        - uuid: {get_uuid(f'{mode}:discovery:sources')}
          name: 'Chrony: NTP sources discovery'
          type: DEPENDENT
          key: chrony.sources.discovery
          delay: '0'
          description: 'Low-level discovery of upstream NTP sources from chrony.'
          master_item:
            key: chrony.sources.json
          preprocessing:
            - type: JAVASCRIPT
              parameters:
                - |
{js_discovery}
          item_prototypes:
            - uuid: {get_uuid(f'{mode}:itemproto:state')}
              name: 'Chrony: Source [{{#SOURCE_NAME}}]: State'
              type: DEPENDENT
              key: 'chrony.source.state[{{#SOURCE_NAME}}]'
              delay: '0'
              history: 7d
              trends: '0'
              value_type: CHAR
              description: 'Current sync status of this source (*=peered, +=combined, -=excluded, ?=unreachable, x=falseticker, ~=jittery).'
              master_item:
                key: chrony.sources.json
              preprocessing:
                - type: JSONPATH
                  parameters:
                    - '$.["{{#SOURCE_NAME}}"].state'
              valuemap:
                name: 'Chrony Source State'
              tags:
                - tag: component
                  value: ntp-source
                - tag: source
                  value: '{{#SOURCE_NAME}}'
              trigger_prototypes:
                - uuid: {get_uuid(f'{mode}:triggerproto:falseticker')}
                  expression: 'last(/{tpl_name}/chrony.source.state[{{#SOURCE_NAME}}])="x"'
                  name: 'Chrony: NTP source [{{#SOURCE_NAME}}] is flagged as false ticker'
                  priority: WARNING
                  description: 'Chrony has flagged this source as inconsistent or erroneous (falseticker).'
                  tags:
                    - tag: component
                      value: ntp-source

            - uuid: {get_uuid(f'{mode}:itemproto:stratum')}
              name: 'Chrony: Source [{{#SOURCE_NAME}}]: Stratum'
              type: DEPENDENT
              key: 'chrony.source.stratum[{{#SOURCE_NAME}}]'
              delay: '0'
              history: 7d
              value_type: UNSIGNED
              description: 'NTP Stratum level reported by this source.'
              master_item:
                key: chrony.sources.json
              preprocessing:
                - type: JSONPATH
                  parameters:
                    - '$.["{{#SOURCE_NAME}}"].stratum'
              tags:
                - tag: component
                  value: ntp-source
                - tag: source
                  value: '{{#SOURCE_NAME}}'

            - uuid: {get_uuid(f'{mode}:itemproto:reach')}
              name: 'Chrony: Source [{{#SOURCE_NAME}}]: Reachability register'
              type: DEPENDENT
              key: 'chrony.source.reach[{{#SOURCE_NAME}}]'
              delay: '0'
              history: 7d
              value_type: UNSIGNED
              description: '8-bit reachability register converted from octal to decimal (0 = no response to last 8 probes, 255 = 100% reachable).'
              master_item:
                key: chrony.sources.json
              preprocessing:
                - type: JSONPATH
                  parameters:
                    - '$.["{{#SOURCE_NAME}}"].reach_val'
              tags:
                - tag: component
                  value: ntp-source
                - tag: source
                  value: '{{#SOURCE_NAME}}'
              trigger_prototypes:
                - uuid: {get_uuid(f'{mode}:triggerproto:unreachable')}
                  expression: 'last(/{tpl_name}/chrony.source.reach[{{#SOURCE_NAME}}])=0'
                  name: 'Chrony: NTP source [{{#SOURCE_NAME}}] is unreachable'
                  priority: INFO
                  manual_close: 'YES'
                  description: 'All 8 most recent poll attempts to this NTP source failed (reachability register = 0).'
                  tags:
                    - tag: component
                      value: ntp-source

            - uuid: {get_uuid(f'{mode}:itemproto:offset')}
              name: 'Chrony: Source [{{#SOURCE_NAME}}]: Last sample offset'
              type: DEPENDENT
              key: 'chrony.source.offset[{{#SOURCE_NAME}}]'
              delay: '0'
              history: 7d
              value_type: FLOAT
              units: s
              description: 'Estimated clock offset measured from this upstream source in seconds.'
              master_item:
                key: chrony.sources.json
              preprocessing:
                - type: JSONPATH
                  parameters:
                    - '$.["{{#SOURCE_NAME}}"].offset'
              tags:
                - tag: component
                  value: ntp-source
                - tag: source
                  value: '{{#SOURCE_NAME}}'

            - uuid: {get_uuid(f'{mode}:itemproto:delay')}
              name: 'Chrony: Source [{{#SOURCE_NAME}}]: Root distance / delay'
              type: DEPENDENT
              key: 'chrony.source.delay[{{#SOURCE_NAME}}]'
              delay: '0'
              history: 7d
              value_type: FLOAT
              units: s
              description: 'Total network distance / round-trip delay to this source in seconds.'
              master_item:
                key: chrony.sources.json
              preprocessing:
                - type: JSONPATH
                  parameters:
                    - '$.["{{#SOURCE_NAME}}"].delay'
              tags:
                - tag: component
                  value: ntp-source
                - tag: source
                  value: '{{#SOURCE_NAME}}'

            - uuid: {get_uuid(f'{mode}:itemproto:poll')}
              name: 'Chrony: Source [{{#SOURCE_NAME}}]: Poll interval'
              type: DEPENDENT
              key: 'chrony.source.poll[{{#SOURCE_NAME}}]'
              delay: '0'
              history: 7d
              value_type: UNSIGNED
              description: 'Polling interval for this source expressed as log2 value (e.g. 6 = 64s, 10 = 1024s).'
              master_item:
                key: chrony.sources.json
              preprocessing:
                - type: JSONPATH
                  parameters:
                    - '$.["{{#SOURCE_NAME}}"].poll'
              tags:
                - tag: component
                  value: ntp-source
                - tag: source
                  value: '{{#SOURCE_NAME}}'

          graph_prototypes:
            - uuid: {get_uuid(f'{mode}:graphproto:metrics')}
              name: 'Chrony: Source [{{#SOURCE_NAME}}] offset and delay'
              graph_items:
                - color: 199C0D
                  item:
                    host: '{tpl_name}'
                    key: 'chrony.source.offset[{{#SOURCE_NAME}}]'
                - sortorder: '1'
                  color: F63100
                  item:
                    host: '{tpl_name}'
                    key: 'chrony.source.delay[{{#SOURCE_NAME}}]'

      macros:
        - macro: '{{$CHRONY.OFFSET.WARN}}'
          value: '0.1'
          description: 'Warning threshold for system clock offset in seconds (0.1 = 100ms).'
        - macro: '{{$CHRONY.OFFSET.CRIT}}'
          value: '0.5'
          description: 'Critical threshold for system clock offset in seconds (0.5 = 500ms).'
        - macro: '{{$CHRONY.SOURCES.MIN.WARN}}'
          value: '2'
          description: 'Minimum required synchronized NTP sources.'

      valuemaps:
        - uuid: {get_uuid(f'{mode}:valmap:leap')}
          name: 'Chrony Leap Status'
          mappings:
            - value: '0'
              newvalue: Normal
            - value: '1'
              newvalue: 'Insert second'
            - value: '2'
              newvalue: 'Delete second'
            - value: '3'
              newvalue: 'Not synchronised'

        - uuid: {get_uuid(f'{mode}:valmap:state')}
          name: 'Chrony Source State'
          mappings:
            - value: '*'
              newvalue: 'Current synchronized source'
            - value: '+'
              newvalue: 'Combined / Candidate'
            - value: '-'
              newvalue: 'Excluded / Outlier'
            - value: '?'
              newvalue: Unreachable
            - value: 'x'
              newvalue: 'False ticker (erroneous time)'
            - value: '~'
              newvalue: 'Jitter too variable'

        - uuid: {get_uuid(f'{mode}:valmap:mode')}
          name: 'Chrony Source Mode'
          mappings:
            - value: '^'
              newvalue: Server
            - value: '='
              newvalue: Peer
            - value: '#'
              newvalue: 'Reference clock'

  graphs:
    - uuid: {get_uuid(f'{mode}:graph:offsets')}
      name: 'Chrony: System clock offsets'
      graph_items:
        - color: 199C0D
          item:
            host: '{tpl_name}'
            key: chrony.tracking.offset.system
        - sortorder: '1'
          color: F63100
          item:
            host: '{tpl_name}'
            key: chrony.tracking.offset.rms
        - sortorder: '2'
          color: 2774A4
          item:
            host: '{tpl_name}'
            key: chrony.tracking.offset.last

    - uuid: {get_uuid(f'{mode}:graph:delay')}
      name: 'Chrony: Root delay and dispersion'
      graph_items:
        - color: 199C0D
          item:
            host: '{tpl_name}'
            key: chrony.tracking.root_delay
        - sortorder: '1'
          color: F63100
          item:
            host: '{tpl_name}'
            key: chrony.tracking.root_dispersion

    - uuid: {get_uuid(f'{mode}:graph:freq')}
      name: 'Chrony: Frequency and skew'
      graph_items:
        - color: 199C0D
          item:
            host: '{tpl_name}'
            key: chrony.tracking.freq_ppm
        - sortorder: '1'
          color: F63100
          item:
            host: '{tpl_name}'
            key: chrony.tracking.skew_ppm
"""
    return out

# Generate passive
with open(os.path.join(SCRIPT_DIR, 'template_chrony_agent2_passive.yaml'), 'w', encoding='utf-8') as f:
    f.write(generate_yaml(active=False))

# Generate active
with open(os.path.join(SCRIPT_DIR, 'template_chrony_agent2_active.yaml'), 'w', encoding='utf-8') as f:
    f.write(generate_yaml(active=True))

print("Both templates generated successfully!")
