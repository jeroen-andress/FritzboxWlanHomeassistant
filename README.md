# Fritz!Box 7412 WLAN switch  for Home Assistant

[Home Assistant](https://www.home-assistant.io) component, switch your WLAN on and off on a Fritz!Box 7412.

## Installation

1.  Either checkout this repository using `git clonegit@github.com:jeroen-andress/firtzbox_wlan_homeassistant.git`
2. Copy the created folder `firtzbox_wlan_homeassistant` to your configuration folder under `<config>/custom_components/`. This folder may still need to be created. The `configuration.yaml` is also located in `<config>`.
3. Restart your home assistant.

## Configuration

To be able to use this component, add the following configuration to your `configuration.yaml`:

```
switch:
  - platform: wlan_fritzbox_7412
    url: fritz.box
    password: !secret fritzbox_pass
    ssid: FRITZ!Box 7412
```

Here is a description of the values possible:

Parameter|Default values|Description|Optional|
---------|--------------|-------------|------|
url|fritz.box|Hostname of your Fritz!Box 7412|Yes
password||Password of your Fritz!Box 7412. It is best to save it in the ``secrets.yaml`` file.|No
ssid||SSID of your WLAN. Check your configuration for it.|No

## Troubleshooting

When the component is loaded, an entry is written in the Home Assistant log: ``WLAN FRITZ!Box 7412 created with hostname <hostname>, ssid <SSID> and init state True``. If this entry cannot be found, the component has not been loaded. Check the configuration.

Whether the WLAN is on or off is stored in the system persistently. At the first start-up, this state is assumed to be _ON_. Therefore, it may be necessary to manually switch the WLAN on or off in the Fritz Box in order to synchronise the two states.