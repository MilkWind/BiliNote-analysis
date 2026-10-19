## 目录
- 跨域携带 Cookie 的整体思路 *Content-[00:00]
- 前端请求的具体实现 *Content-[02:20]
- 服务端响应与配置的具体实现 *Content-[04:39]
- AI 总结

## 跨域携带 Cookie 的整体思路 *Content-[00:00]

在跨域请求中携带另外一个域名下的 Cookie，需要前后端配合，同时满足以下四个核心条件：

1\. **前端请求配置**：
   - 使用 `XMLHttpRequest` 时，需要设置 `withCredentials = true`。
   - 使用 `fetch` 请求时，需要设置 `credentials: 'include'`。

2\. **服务端响应头配置 (Credentials)**：
   - 服务端必须在响应头中设置 `Access-Control-Allow-Credentials: true`，明确允许请求携带凭证。

3\. **服务端响应头配置 (Origin)**：
   - `Access-Control-Allow-Origin` **不能**设置为通配符 `*`（因为携带凭证时设置通配符是不安全的）。
   - 必须指定对应的允许的来源（Origin）。在实际开发中，可以枚举多个安全的域名进行配置。

4\. **Cookie 属性配置**：
   - Cookie 的 `SameSite` 属性需要设置为 `None`，允许跨站发送。
   - 必须同时设置 `Secure` 属性，这意味着该 Cookie 只能在 HTTPS 链接中使用，以保证传输安全。

## 前端请求的具体实现 *Content-[02:20]

在前端发起请求时，不同的请求库或 API 需要进行相应的配置以开启凭证携带：

1\. **使用 XMLHttpRequest**：
   - 通过 `new XMLHttpRequest()` 创建 XHR 对象。
   - 使用 `open` 方法建立链接，传入三个参数：请求方法（如 GET/POST）、API 地址、是否异步（如 `true` 表示异步）。
   - **关键配置**：在 XHR 对象上设置 `xhr.withCredentials = true`。如果不进行此设置，浏览器不会主动携带当前域名下的 Cookie 给服务端。

2\. **使用 fetch API**：
   - 在调用 `fetch` 函数时，需要传入配置对象。
   - **关键配置**：设置 `credentials: 'include'`，以指示浏览器在跨域请求中包含 Cookie。

3\. **使用 Axios**：
   - 配置逻辑与 `XMLHttpRequest` 同理。
   - **关键配置**：在 Axios 的请求配置中设置 `withCredentials: true`。

## 服务端响应与配置的具体实现 *Content-[04:39]

服务端在下发响应时，需要进行严格的 CORS（跨域资源共享）相关 Header 配置，以确保安全性和功能的实现：

1\. **基础 CORS 配置**：
   - `Access-Control-Allow-Origin`：必须设置为具体的域名（如 `https://example.com`），绝对不能使用通配符 `*`。
   - `Access-Control-Allow-Credentials: true`：允许客户端携带凭证（Cookie）。

2\. **允许请求的方法 (Methods)**：
   - 通过 `Access-Control-Allow-Methods` 限制和允许客户端使用的请求方法。
   - 常见允许的方法包括：`GET`、`POST`、`PUT`、`DELETE`。
   - **必须包含 `OPTIONS`**：因为跨域请求在触发预检机制时，会先发起 `OPTIONS` 预检请求，服务端必须允许该方法。

3\. **允许请求头 (Headers)**：
   - 通过 `Access-Control-Allow-Headers` 允许客户端在请求中设置相关的自定义请求头。
   - 常见允许的头包括：`Origin`、`X-Requested-With`、`Content-Type` 等。
   - 通过这些白名单设置进行安全性校验，将非安全的请求头拦截在摇篮中。

4\. **预检请求 (OPTIONS) 处理**：
   - 当拦截到请求方法为 `OPTIONS`（预检请求）时，服务端不需要执行具体的业务逻辑。
   - 直接返回 `200` 状态码，告知浏览器预检通过，然后继续执行下一个中间件即可。

## AI 总结

在跨域场景下携带其他域名的 Cookie，核心在于**前后端的凭证授权**与**Cookie 的安全属性**配合。前端需通过 `withCredentials` 或 `credentials: 'include'` 开启凭证携带；后端需配置 `Access-Control-Allow-Credentials: true`，且 `Access-Control-Allow-Origin` 必须为具体域名（禁用 `*`）。同时，目标 Cookie 必须满足 `SameSite=None` 且带有 `Secure` 属性（仅限 HTTPS 环境）。此外，后端需正确放行 `OPTIONS` 预检请求，并合理配置允许的 Methods 和 Headers 以保障跨域通信的安全与顺畅。

---

## 文稿转写

好同学们 接下来我们来看一下 就需要在我们跨域请求中 携带另外一个域名下的cookie 我们该如何操作呢 就是这种cookie的一个思路内容 我们在跨域请求中携带另外一个域名的cookie啊 我们需要同时满足以下几个条件 首先我们在前端发请求的时候 我们需要设置对应的xl h p request 或者是我们进行fetch请求的时候 我们需要设置CREDENT Credence 我们需要设置为include Include 这是第一步我们需要做的一个事情 那么我们服务端需要在响应头中设置我们的呃 ACAACAC的时候 我们设置为true 就我们a size control A more alone credence 我们必须设置为数 第三步呢 我们需要在服务端的asset control law origin 然后不能设置对应通配符 我们必须指定对应的允许的原 因为设置通配符是不安全的 我们可以设置为多个多个圆 这样的话啊 把多个我们比较安全的这个域名给它去枚举掉 所以这是我们常见的一个思路 More access control 第四步呢就对于我们需要携带cookie的时候啊 携带cookie的时候 我们的same side写在规模需要设置为none 并且呢我们需要同时设置对应的a cure 这样的属性 这个安全属性呢 我们只能在我们HB链接区区去使用 我们可以进行这样的一个设置 TPS在句中使用 哦这是我们整体的一个思路啊 那么我们看看具体的一个扩展该怎么去实现 首先第一步我们使用timeout it is request去进行配置 我们一般之前也讲过 我们可以使用XML rekp request 来去模拟对应的ITS请求 这也是通篇需要额外去注意的 它整个的流程 我们需要通过new我们XML hp quest 创建这个X1X这个对象 叉一叉对象呢 我们通过open的方式去建立对应的一个发起 对应的链接 第一个我们需要传入对应的方法啊 第二步就是对应的API 第三个就是我们的是是否是异步的 比如true就是否设置为think 就是异步的之后 我们需要在我们鲨鱼其他啊 去配置我们的with credence With credals 我们设置为true 这样的话才会能够携带当前的cooking 否则的话他不会主动去哦 携带对应的cookie给我们服务端 那么这样的设置的话 我们就能够携带对应的cookie的信息 给到我们当前服务端 或者如果我们这是通过叉叉叉对象 我们如果你通过fish的话 我们就需要哦在我们fish函数的调用的时候 也需要传入对应的这样的配置 设置credinate the true 好 那么我使用EXOS的话 同理啊 都是一个配置 那么我们接下来就是我们服务端相关的一 些配置 我们服务端刚刚说了 就需要 服务端下发的时候 就需要进行设一些header的相关的配置 我们就要设置对应的request request header 我们assize control A low ranging 我们设置对应的具体的一些源 具体的域名 就不能设置通配符 并且呢我们需要设置允许携带凭证 允许写这对应的凭证 好接下来我们就是还需要设置一些语 一些通用的嗯 请求允许请求的方法 这就是我们可以限制一些方法的一个调用 我们可以设置对应的get呀 post呀 一些常见的请求 我们都可以去允许put呀 Delete 还有我们options 我们遇见请求需要发起对应的options 所以我们option options也需要进行相应的配置 那么我们可以也可以设置对应的允许请求图 这都是我们服务端这边的常常规的一个设置 我们在headers当中通过设置和3s allow headers 那么就允许让我们在客户端去设置 相关的一些请求头 比如arranging 还有我们charge request with 以及我们的content type 通过这样的设置来去约束 进行一些安全性的一些校验 把些啊非安全性的相关的请求啊 或者相同的设置啊 去扼杀在我们的摇篮当中 那么我们还有对应的 如果当前是methods 就是当前是option 我们的预检请求发起对应的option 那么我们就需要返回 反而对应的状态两两百的状态码 最后我们执行执行它的下一个呃中间键好 这是我们常见的这样的一个整体的一个思路
