# Attribution and license / 来源与许可

- Upstream project: [Insta360 Luna Ultra Reverse Engineering](https://github.com/derrickyau9/insta360-luna-ultra-reverse-engineering).
- Upstream author/account: [derrickyau9](https://github.com/derrickyau9).
- Upstream revision used for this local adaptation: `92f5e7afadb6693054f0547031aa90dc54cb08ed`.
- License: [Apache License 2.0](../../LICENSE), retained unchanged from upstream.
- Original upstream README: [Luna Ultra documentation](../../LUNA_UPSTREAM.md), preserved in a separate document.
- Protocol references retained in this repository: [Wi-Fi bootstrap documentation](../../docs/wifi-root-shell.md) and [upstream helper](../../scripts/wifi-root-shell.py).

The upstream project documents the GUI command interface used by this X6 adaptation. Credit for that published interface remains with its upstream authors; this branch does not claim its discovery.

Added on 2026-10-24: the X6 v0.8.825 client, local pairing and identity checks, bounded command-result verification, tests, and Chinese/English X6 instructions. The root README was rewritten as the X6 project homepage. Upstream device scripts, service units, documentation and license were retained. The original README content is preserved without edits in [LUNA_UPSTREAM.md](../../LUNA_UPSTREAM.md), below a device-scope notice.

The X6 additions are distributed under the same Apache-2.0 license. The X6 documentation's hardware and simulation qualifications apply only to X6; upstream Luna validation does not establish X6 compatibility. Do not run Luna installation, uninstallation or USB configuration scripts on X6.

上游作者及协议出处如上。本分支新增 X6 v0.8.825 客户端、配对与身份检查、命令结果验证、测试和中英文说明；没有将上游公开入口声称为本分支原创发现。根 README 改为 X6 项目首页；原始 README 全文移至 [LUNA_UPSTREAM.md](../../LUNA_UPSTREAM.md)，正文未改动，仅在前面增加机型适用范围说明。上游其他文件及历史予以保留，许可证未修改。X6 新增内容采用相同的 Apache-2.0 许可证。Luna 的测试结果不代表 X6 兼容；不要在 X6 上运行 Luna 安装、卸载或 USB 配置脚本。
