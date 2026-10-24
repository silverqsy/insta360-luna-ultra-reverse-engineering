# Insta360 X6 Research

Tools and documentation for researching the Insta360 X6, starting with local root command verification. The X6 Python client runs on your computer and requires no SDK.

## Get started

**[English guide](devices/x6/README.en.md) · [中文使用指南](devices/x6/README.md)**

Use the tools in `devices/x6`. Do not run the repository's Luna installation, uninstallation or USB configuration scripts, or install Luna services, on an X6.

## Supported firmware

**X6 v0.8.825 only.** For first access, keep the camera unactivated and connect directly to its first-boot Wi-Fi. Do not connect the official app or complete official activation, which can require a firmware update.

The method was verified on one v0.8.825 camera. The public client's tests use simulated camera responses; support for later firmware, persistent root, updates and recovery has not been established. This project currently provides no X6 firmware installer.

## Acknowledgements and license

Thank you to [derrickyau9](https://github.com/derrickyau9) and the upstream contributors for sharing their Luna Ultra research, GUI protocol documentation and tools, which provided the protocol reference for this X6 adaptation.

Forked from [Insta360 Luna Ultra Reverse Engineering](https://github.com/derrickyau9/insta360-luna-ultra-reverse-engineering), revision `92f5e7a`. The [original Luna README](LUNA_UPSTREAM.md), upstream history and [Apache-2.0 license](LICENSE) are retained. See [Attribution and license / 来源与许可](devices/x6/ATTRIBUTION.md) for details.
