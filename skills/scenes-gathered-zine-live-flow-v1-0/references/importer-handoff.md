# 实况照片导入器交接

## 输入合同

- 只向导入器提交一个 `.zip` 文件。
- ZIP 顶层包含一个文件夹；该文件夹内只放一组已配对的 `.JPG` 与 `.MOV`。
- 不把渲染回执、接触表、源海报或其他文件放进 ZIP。
- JPG 与 MOV 使用配对脚本生成的同一资源标识。

## 自动交接

运行 `scripts/build_live_zip_and_import.py`。脚本把所有中间产物放在临时目录，只把最终 ZIP 移到指定输出路径，然后通过 macOS 文件打开机制把 ZIP 交给 bundle id 为 `com.zeejay.live-photo-importer` 的“实况照片导入器”。

Skill 已内置 `assets/实况照片导入器.app`，适用于 macOS 13 及以上的 Apple 芯片 Mac。脚本依次查找显式指定的应用、环境变量路径、`/Applications`、用户 `Applications` 与该内置应用，无需另行下载。首次运行时，macOS 可能请求打开应用或访问照片图库的权限；让用户在系统提示中决定。

导入器已原生支持 ZIP 文件打开事件；不要模拟拖拽或操作“照片”App。ZIP 成功提交给导入器即为本技能的停止点。照片配对、图库权限提示、写入图库和后续同步均由导入器负责。

如果内置导入器缺失，可用 `--importer-app /absolute/path/实况照片导入器.app` 或环境变量 `LIVE_PHOTO_IMPORTER_APP` 指定另一份。若交接失败，保留已生成的 ZIP 并报告错误，不要重新生成画面。

## 无副作用测试

使用 `--no-import` 只构建 ZIP，不打开导入器。可调用导入器二进制的 `--scan <zip>` 检查它能否识别一组配对资源；扫描不会写入照片图库。
