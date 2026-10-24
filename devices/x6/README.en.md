# Insta360 X6 v0.8.825: local root command verification

[Project home](https://github.com/silverqsy/insta360-x6-research) · [中文](README.md) · [Attribution and license](ATTRIBUTION.md)

> **X6 entry point: use only this directory's Python tool, on your computer. Do not run the repository-root `scripts/install.sh`, `scripts/uninstall.sh` or `device/enable-usb-adb.sh` on an X6, and do not install any `luna-*.service` units.** These upstream scripts target Luna Ultra, modify ADB services or USB configuration, and have not been validated on X6.
>
> X6 adaptation added on 2026-10-24. See [ATTRIBUTION.md](ATTRIBUTION.md) for the upstream project, author and protocol source. This adaptation uses the repository's [Apache-2.0 license](../../LICENSE).

For an X6 that you own and are authorized to operate. **Firmware must be v0.8.825.** Earlier testing on one camera running this version confirmed that its GUI debug interface could execute `id` with `uid=0(root)` and remained accessible after a normal reboot. This finding does not apply to v1.0.20 or v1.2.36, and does not establish that access survives an official update.

This directory contains a standalone Python implementation of that method, with no SDK dependency. The public tool has passed unit tests and a simulated-camera `pair → probe → run` workflow, including failure cases, in a fresh Python virtual environment. The simulation uses local TCP connections, synthetic identity and simulated root output; it is not additional hardware validation. The public tool has not yet been fully tested on another camera. It installs no service, flashes no firmware, and provides no guarantee of persistent root or recovery.

## Prerequisites

- A macOS or Linux terminal with Python 3.10 or newer. No third-party Python packages or `pip install` step is needed. This clean-environment check used macOS / Python 3.13.
- This guide records first access on an unactivated camera: leave it at the first-boot screen asking you to connect to the official app, and use the Wi-Fi already enabled at that point. **Do not connect the official app or complete official activation: that setup flow can require a firmware update and remove the old-firmware entry point.**
- You do not need to open Camera Info or reach the normal shooting interface. `pair` first checks the model and firmware through a read-only query and proceeds only on v0.8.825. The tool does not change activation state or trigger firmware updates.
- Connect the computer directly to the target camera's first-boot Wi-Fi. The computer should receive a `192.168.42.*` address; the camera is at `192.168.42.1`. Use a direct network under the owner's control. If the hotspot is unavailable, stop; do not connect the official app as a workaround.
- Allow Python to receive a local TCP callback from the camera on a temporary port. The camera's control port is 6666 and its GUI debug port is 23456. The tool connects only to the fixed camera address and does not scan the network.

Connection authorization is a prerequisite enforced by this tool. It does not mean that the old GUI debug interface itself enforces the same authorization. The transport is unencrypted.

Obtain this adaptation branch and **open an interactive terminal at the repository root**. Run the following commands to enter `devices/x6`. Run all subsequent `pair`, `probe` and `run` commands from that directory. Computer-side `sudo` is unnecessary; do not copy the repository onto the camera. These tests do not connect to a camera:

```sh
cd devices/x6
python3 --version
python3 -m unittest -v
```

All tests should pass. If `python3` is unavailable, install Python 3.10 or newer before proceeding.

## 1. Pair

```sh
python3 x6_root.py pair
```

When prompted, enter the complete serial number from this camera's body label or its matching original packaging to verify the target. Input is hidden. You do not need to activate the camera or enter its menus to obtain it. If the camera asks to authorize the connection, tap Allow within 60 seconds. Expect `Paired locally`.

The tool creates `.x6-owner-state.json` in the **current directory**, containing a client identifier and a hash of the serial number. It creates the file with read/write permissions for the local user only. Keep it for subsequent commands; do not upload or share it. Pairing is ordinary connection authorization, not official product activation. Do not repeat `pair` when the pairing file already exists.

## 2. Verify root

```sh
python3 x6_root.py probe
```

Expected success output:

```text
Verified: uid=0(root)
```

The tool executes `/usr/bin/id` and checks root identity, fresh response markers and command completion. `Pack success`, an open port or a device listing is insufficient. Before execution, it checks the firmware version, paired identity and connection authorization; afterward, it checks identity again.

## 3. Run a short command

Create a UTF-8 command file, then run it. `EOF` terminates the terminal input block; it is not part of the camera command:

```sh
cat > command.txt <<'EOF'
/usr/bin/id
EOF
python3 x6_root.py run --command-file command.txt
```

Expect `Verified: uid=0(root)` followed by the command's own `uid=0(root)` output. The command runs on the camera. Each `run` invocation performs a separate root check before executing the command file.

The tool captures standard output only, not standard error, and is not an interactive terminal. Each callback waits up to approximately 20 seconds and accepts at most 64 KiB of standard output. Overlong commands are rejected before connecting. Nonzero command status, missing completion markers and truncated callbacks produce an error and a nonzero CLI exit code. **A timeout ends the computer's wait; it does not guarantee termination of the command on the camera. Use short commands, and do not blindly repeat operations with side effects after a timeout.** An earlier successful root check does not mean the subsequent custom command succeeded.

To test writing, reading and deleting a disposable file, replace the command file with the following and run it. This creates a randomly named temporary file and cleans it up on exit:

```sh
cat > command.txt <<'EOF'
p=$(/bin/busybox mktemp /tmp/x6-check.XXXXXX) || exit 1
trap 'rm -f "$p"' EXIT
printf 'owner-check\n' > "$p" && [ "$(cat "$p")" = owner-check ] && rm -f "$p" && printf 'write/read/delete OK\n'
EOF
python3 x6_root.py run --command-file command.txt
```

Expect `write/read/delete OK`. This verifies temporary-directory writes. Root access does not mean system partitions are writable, or that firmware will remain modifiable after an update.

## Recheck after reboot

Ensure no update is running and no update package is pending, then use the camera's normal power controls to reboot. Reconnect to its Wi-Fi, keep the pairing file in the same working directory, and repeat `probe` and the temporary-file test. If either fails, stop. Do not upgrade, downgrade or switch slots to try to restore access. Success with this tool alone does not establish a usable recovery path.

## Troubleshooting

- Connection timeout: confirm the computer is still connected to camera Wi-Fi and the hotspot has not shut down automatically.
- Callback timeout: check that the firewall allows Python to receive the camera's callback. A `Pack success` response alone does not confirm execution.
- Firmware or identity mismatch: stop and check the camera or matching packaging label and the connected hotspot. The tool rejects a mismatched device or firmware. Do not edit the script to skip these checks or use official activation or an update as a workaround.
- `Run pair first`: check the current directory and confirm that it contains your local pairing file.
- Authorization denied: copy the tool and test files into a new working directory, run `pair` again, and approve on the camera. Keep the old pairing file in its original directory.
- Invalid pairing file: do not edit the identity hash; pair again in a new working directory.
- Nonzero exit status or completion-marker error: command success was not confirmed. Check the command and camera state before continuing; the earlier root-check line is insufficient.
- No verified `uid=0`, or connection refused: access has not been verified under the current conditions. Do not use this result as a basis for flashing other firmware.
