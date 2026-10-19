# 【金九银十】前端面试场景题：跨域请求中携带另一个域名下的 Cookie

## 目录
- 1. 跨域携带 Cookie 的核心条件 *Content-[00:00]
- 2. 前端请求的具体实现 *Content-[02:22]
- 3. 服务端响应头的配置与预检请求 *Content-[04:40]
- AI 总结

## 1. 跨域携带 Cookie 的核心条件 *Content-[00:00]

在跨域请求中携带另外一个域名下的 Cookie，需要前后端同时配合，必须满足以下四个核心条件：

1\. **前端请求配置凭证**
   - 使用 `XMLHttpRequest` 发请求时，需要设置 `withCredentials = true`。
   - 使用 `fetch` 请求时，需要设置 `credentials: 'include'`。

2\. **服务端允许携带凭证**
   - 服务端需要在响应头中设置 `Access-Control-Allow-Credentials: true`，明确允许请求携带凭证（Cookie）。

3\. **服务端严格限制允许源（Origin）**
   - 服务端的 `Access-Control-Allow-Origin` **不能**设置通配符 `*`。
   - 因为设置通配符是不安全的，必须指定具体允许的源（Origin）。
   - 可以枚举多个安全的域名，将多个比较安全的域名配置进去。

4\. **Cookie 属性配置**
   - 当需要跨域携带 Cookie 时，Cookie 的 `SameSite` 属性必须设置为 `None`。
   - 同时必须设置 `Secure` 安全属性，这意味着该 Cookie 只能在 `HTTPS` 链接中使用。

## 2. 前端请求的具体实现 *Content-[02:22]

在明确了核心条件后，前端可以通过不同的请求方式来实现配置：

1\. **使用 XMLHttpRequest (XHR)**
   - 通过 `new XMLHttpRequest()` 创建 XHR 对象。
   - 使用 `open(method, url, isAsync)` 方法建立连接（例如传入 `true` 表示异步请求）。
   - 在 `send` 方法执行前，配置 `xhr.withCredentials = true`。如果不进行此设置，浏览器不会主动携带当前域名下的 Cookie 给服务端。

2\. **使用 Fetch API**
   - 在调用 `fetch` 函数时，传入配置对象。
   - 在配置中设置 `credentials: 'include'`，以确保携带 Cookie 信息。

3\. **使用 Axios**
   - 如果使用 `axios` 等第三方库，同理也需要在请求配置中开启 `withCredentials: true`。

## 3. 服务端响应头的配置与预检请求 *Content-[04:40]

服务端在下发响应时，需要进行一系列 Header 的相关配置，以确保跨域请求的安全性和合法性：

1\. **基础 CORS 响应头配置**
   - 设置 `Access-Control-Allow-Origin` 为具体的域名（严禁使用 `*` 通配符）。
   - 设置 `Access-Control-Allow-Credentials: true` 允许携带凭证。

2\. **限制允许的请求方法 (Methods)**
   - 通过 `Access-Control-Allow-Methods` 限制并允许特定的请求方法。
   - 常见的允许方法包括：`GET`、`POST`、`PUT`、`DELETE`。
   - **必须包含 `OPTIONS`**：因为跨域请求在特定条件下会发起预检请求（Preflight Request），必须允许 `OPTIONS` 方法。

3\. **限制允许的请求头 (Headers)**
   - 通过 `Access-Control-Allow-Headers` 允许客户端设置的相关请求头。
   - 常见的允许头包括：`Origin`、`X-Requested-With`、`Content-Type` 等。
   - 目的：通过这样的设置来约束安全性校验，将非安全性的请求扼杀在摇篮中。

4\. **处理 OPTIONS 预检请求**
   - 当客户端发起 `OPTIONS` 预检请求时，服务端需要拦截并处理。
   - 处理逻辑：直接返回 `200` 状态码，然后执行下一个中间件（`next()`），无需返回具体业务数据。

## AI 总结

在跨域场景下携带另一个域名的 Cookie 是一个经典的前端面试场景题。其核心在于**前后端的严格配合与安全校验**：
1. **前端**必须显式声明携带凭证（`withCredentials` 或 `credentials: 'include'`）。
2. **后端**必须明确允许凭证（`Allow-Credentials: true`），且**绝对不能**使用 `*` 来放行 Origin，必须指定具体的白名单域名。
3. **Cookie 本身**的属性必须满足 `SameSite=None` 且配合 `Secure`（即必须在 HTTPS 环境下）。
4. 此外，服务端还需妥善处理 `OPTIONS` 预检请求，并合理配置允许的 Methods 和 Headers，以保障跨域通信的安全性。

---

## 文稿转写

好同学们 接下来我们来看一下 就需要在我们跨域请求中 携带另外一个域名下的cookie 我们该如何操作呢 就是这种cookie的一个思路内容 我们在跨域请求中携带另外一个域名的cookie啊 我们需要同时满足以下几个条件 首先我们在前端发请求的时候 我们需要设置对应的xl h p request 或者是我们进行fetch请求的时候 我们需要设置CREDENT Credence 我们需要设置为include Include 这是第一步我们需要做的一个事情 那么我们服务端需要在响应头中设置我们的呃 ACAACAC的时候 我们设置为true 就我们a size control A more alone credence 我们必须设置为数 第三步呢 我们需要在服务端的asset control law origin 然后不能设置对应的通配符 我们必须指定对应的允许的原 因为设置通配符是不安全的 我们可以设置为多个多个圆 这样的话啊 把多个我们比较安全的这个域名给它去枚举掉 所以这是我们常见的一个思路 More access control 第四步呢就对于我们需要携带cookie的时候啊 携带cookie的时候 我们的same side写在规模需要设置为none 并且呢我们需要同时设置对应的a cure 这样的属性 这个安全属性呢 我们只能在我们HB链接区区去使用 我们可以进行这样的一个设置 TPS在句中使用 哦这是我们整体的一个思路啊 那么我们看看具体的一个扩展该怎么去实现 首先第一步我们使用timeout it is request去进行配置 我们一般之前也讲过 我们可以使用XML rekp request 来去模拟对应的ITS请求 这也是通篇需要额外去注意的 它整个的流程 我们需要通过new我们XML hp quest 创建这个X1X这个对象 叉一叉对象呢 我们通过open的方式去建立对应的一个发起 对应的链接 第一个我们需要传入对应的方法啊 第二步就是对应的API 第三个就是我们的是是否是异步的 比如true就是否设置为think 就是异步的之后 我们需要在我们鲨鱼其他啊 去配置我们的with credence With credals 我们设置为true 这样的话才会能够携带当前的cooking 否则的话他不会主动去哦 携带对应的cookie给我们服务端 那么这样的设置的话 我们就能够携带对应的cookie的信息 给到我们当前服务端 或者如果我们这是通过叉叉叉对象 我们如果你通过fish的话 我们就需要哦在我们fish函数的调用的时候 也需要传入对应的这样的配置 设置credinate the true 好 那么我使用EXOS的话 同理啊 都是一个配置 那么我们接下来就是我们服务端相关的一 些配置 我们服务端刚刚说了 就需要 服务端下发的时候 就需要进行设一些header的相关的配置 我们就要设置对应的request request header 我们assize control A low ranging 我们设置对应的具体的一些源 具体的域名 就不能设置通配符 并且呢我们需要设置允许携带凭证 允许写这对应的凭证 好接下来我们就是还需要设置一些语 一些通用的嗯 请求允许请求的方法 这就是我们可以限制一些方法的一个调用 我们可以设置对应的get呀 post呀 一些常见的请求 我们都可以去允许put呀 Delete 还有我们options 我们遇见请求需要发起对应的options 所以我们option options也需要进行相应的配置 那么我们可以也可以设置对应的允许请求图 这都是我们服务端这边的常常规的一个设置 我们在headers当中通过设置和3s allow headers 那么就允许让我们在客户端去设置 相关的一些请求头 比如arranging 还有我们charge request with 以及我们的content type 通过这样的设置来去约束 进行一些安全性的一些校验 把一些呃非安全性的相关的请求啊 或者相同的设置啊 去扼杀在我们的摇篮当中 那么我们还有对应的 如果当前是methods 就是当前是option 我们的预检请求发起对应的option 那么我们就需要返回 反而对应的状态两两百的状态码 最后我们执行执行它的下一个呃中间键好 这是我们常见的这样的一个整体的一个思路
