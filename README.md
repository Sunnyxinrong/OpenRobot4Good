# OpenRobot4Good

可按机器人本体、移动方式、人形尺寸、末端执行器和采集终端检索的机器人训练数据目录。每一行对应发布者描述的一个子集及采集方式。同一个发布可以有多行。22 个配置来自 13 条发布记录，归属 12 个资源家族。11 条来自原工作簿，另补充了一个轮式发布和一个单独发布的四足仿真资源。核查日期为 2026 年 11 月 7 日。

[可筛选目录 CSV](results/catalog.csv) · [类别计数](results/coverage.csv) · [数据许可和版本](data/releases.csv) · [逐项来源和定位](data/sources.csv)

| 检索项 | 配置示例 | 可以复核的内容 |
|---|---|---|
| 轮式 | LeKiwi / sort cubes | 移动底盘与机械臂共存，动作包含夹爪位置、底盘平移速度和转向角速度 |
| 四足 | RoboHive RoboSet Sim / D’Kitty | 仿真专家策略采集的站立任务，留有原始 HDF5 文件头核验记录 |
| 半尺寸人形 | GR00T Sim / Unitree G1 | 参考机型身高 132 cm，所选配置包含腿、腰、臂、手和导航指令 |
| 全尺寸人形 | GR00T Sim / Fourier GR-1 | 参考机型身高 165 cm，CanSort 的发布名称指定 arms-only |
| 灵巧手 | GR00T Panda LiftTray、GR-1 CanSort、NJF Allegro | 不同本体可以使用同一类手，单独的手也可以构成学习对象 |
| 夹爪 | GR00T Panda Threading、LeKiwi、FastUMI | 角色字段区分机器人执行端与手持采集工具 |

人形尺寸采用本目录的身高分组。参考机型站立高度为 110–150 cm 时归入“半尺寸”，160–180 cm 时归入“全尺寸”，两端均包含。其余身高保留原值并标为未分组。尺寸来源和判定依据随记录提供。这里使用的高度来自实体参考机型的规格，任务中的实际运动范围另见 controlled_scope。

采集方式说明轨迹如何产生，终端字段说明操作者怎样发出指令，传感器字段说明记录了什么。DROID 的 Quest 2 是控制终端，腕部与外部相机记录观察。ImitateCholec 的双主操作器发出动作指令，头显提供视觉反馈。MolmoAct2 的参考采集程序支持多个输入设备，当前文件的具体终端保留为未查明。

## 证据范围

7 个配置各核验了 1 个完整 Parquet 文件，保存版本、URL、字节数、SHA-256 和文件尾部行数。D’Kitty 核验了 645,030,315 字节文件的前 512 字节及 HDF5 签名。其余 14 项有发布文档或配置说明。以上计数的单位是配置。RoboSet 真实厨房数据和 RoboHive RoboSet Sim 使用各自的发布 ID，两者共用一个家族标签。

GR00T 的 Panda Threading 显示了查询配置文件的价值。基础元数据使用通用电机名，同一版本的动作映射列出了每侧 3 个相对末端位移分量、3 个轴角旋转分量以及 1 个夹爪闭合指令。[固定版本的动作映射](https://huggingface.co/datasets/nvidia/PhysicalAI-Robotics-GR00T-X-Embodiment-Sim/resolve/ea7ac0b68f87da62f1e726771bba0fe74300802f/bimanual_panda_gripper.Threading/meta/modality.json)

## 使用目录

Python 3.10 及以上版本可以离线生成汇总，命令使用标准库。筛选条件可以组合。

~~~sh
python scripts/catalog.py
python scripts/catalog.py --locomotion wheeled
python scripts/catalog.py --humanoid-size half_size
python scripts/catalog.py --effector-group gripper --effector-role robot
python scripts/catalog.py --terminal spacemouse
~~~

联网复核会先校验发布者数据卡，再检查固定版本的文件。临时文件在验证结束后清理。

~~~sh
python scripts/verify_files.py
python scripts/verify_files.py --configuration grootsim.threading
~~~

| 文件 | 内容 |
|---|---|
| [分类词表](data/taxonomy.json) | 中英文字段、尺寸区间与缺失值定义 |
| [配置记录](data/configurations.csv) | 原始编码、子集、实际控制范围和证据 ID |
| [参考机型身高](data/platform_sizes.csv) | 规格值和出处 |
| [文件核验记录](data/probe_receipts.json) | 固定版本、哈希、完整文件或文件头的核验范围 |
| [轮式补充案例的筛选记录](data/wheeled_discovery.csv) | 检查过的候选及选择理由 |
| [Hub 数据卡模板](hub/README.md) | Dataset Viewer 配置和上游许可说明 |

本仓库沿用项目的 [MIT 许可](LICENSE)。各项 data_license 表示对应原始数据的条款。RoboSet 真实子集的许可覆盖范围仍待核实，状态保存在 license_scope_status 字段中。
