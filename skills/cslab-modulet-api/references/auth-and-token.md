# moduleT 鉴权与令牌生命周期

## 基础约定

- 基础前缀：`${CSLAB_SERVER_HOST}/cslab-server/`，环境变量名以实际项目为准。
- API 响应通常包装为 `{"status": 200, "msg": "成功", "data": ...}`，先判
  `status` 再读取 `data`。
- 认证请求使用 `Authorization: jwt <token>` 和 `DEVICE-TYPE: <device_type>`；服务端
  取空格后的令牌段，前缀大小写不应作为业务依赖。

## 凭据安全

每个新的后台访问任务都重新确认目的和范围。账号、密码、token 与 rtoken 只在当前任务
进程内存中存在，不写文件、不进入命令输出、不从浏览器 localStorage/cookie、日志、历史
文件或 Git 搜集。没有安全输入通道时停止登录并说明限制。

登录授权不等于模板写入授权。写操作还必须满足 `template-maintenance.md` 的业务确认。

## 无 UI 登录

1. `GET auth/image/`，确认 `status=200`，从 `data` 取得 `key`、`x`、`y`。
2. `POST login/`，JSON body 使用 `username`、`password`、`key`、
   `image_verify_code: [x, y]` 和 `device_type`。
3. 确认包装响应成功，只在内存保存 `data.token` 和 `data.rtoken`；输出只说明是否成功。
4. 其他部署要求人工验证码、MFA 或 SSO 时停止自动登录，由开发者完成，不破解或绕过。

## 刷新与 single-flight

- token 有效期由服务端配置；当前部署实测约 900 秒，前端使用约 780 秒提前刷新检查点。
  实际代码以登录/响应时间和部署配置为准，不把该实测值写成跨部署常量。
- 不持续轮询。每次认证请求前检查刷新时间，长时间无请求不产生额外流量。
- 到达检查点后调用 `GET auth/refresh/`，请求头使用 rtoken，而不是旧 token。
- 刷新成功后原子替换 token、rtoken 和下一检查时间；可用 HTTP `Date` 响应头校正时钟。
- 并发请求采用 single-flight，同一时刻只允许一个刷新请求，其余等待后读取新令牌。

刷新网络失败、业务失败、401，或接口返回状态 `40001`（可能为字符串或数字）时，清空
内存中的令牌状态。仍持有当前任务凭据时最多重新登录一次，再失败就停止；不得无限重试、
继续使用已替换的 rtoken 或伪造后台数据。
