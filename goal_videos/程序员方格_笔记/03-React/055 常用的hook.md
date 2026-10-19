## 目录

- 常用 React Router Hooks 概览
- useLoaderData 的重要性与性能优化
- useParams 与 useSearchParams 的使用
- useNavigate 编程式导航与跳转方式
- redirect 组件外部重定向
- useLocation 获取当前路由信息
- useMatch 匹配当前路由规则
- 常见组件 Link 简介
- AI 总结

## 常用 React Router Hooks 概览 *Content-[00:01]

在 React Router 中，提供了多个非常常用的 Hooks 来处理路由相关的逻辑，主要包括：
- `useParams`：用于获取当前路由的动态参数。
- `useNavigate`：用于进行编程式的路由导航与跳转。
- `useLocation`：用于获取当前的路由详细信息。
- `useMatch`：用于匹配当前的路由规则。
- `useLoaderData`：用于获取路由加载时预取的相关数据。

## useLoaderData 的重要性与性能优化 *Content-[00:26]

`useLoaderData` 是 React Router 提供的一个非常重要的特性（在 Vue 中通常不存在类似的原生特性），它能显著提升页面加载性能和用户体验。

**1. 常规串行链路（传统方式）**
在传统的开发思路中，数据获取通常是串行的：
- 首先加载组件。
- 执行组件的生命周期，例如渲染到 `useEffect` 中。
- 等待 DOM 渲染完成。
- 在 `useEffect` 中发起对应的接口请求（fetch）。
- 等待接口数据返回后，重新 render 更新当前组件内容。

**2. 使用 useLoaderData 的优化链路**
利用路由提供的 `loader` 能力，可以改变这种串行模式：
- 在用户点击跳转时，路由层就会提前发起对应的数据请求。
- 等页面渲染完成后，在组件中直接使用 `useLoaderData` 获取数据。
- 无需在组件内部再次等待和发起请求。

**优势**：这种并行或预加载的方式使得页面性能更好，用户等待时间更短，体验更佳。强烈建议在项目中使用此能力。

## useParams 与 useSearchParams 的使用 *Content-[01:31]

在演示这些 Hooks 之前，首先需要确保路由模式配置正确，通常将路由交换为 `BrowserRouter`（即 history 模式）。

**1. useParams**
- 用于获取动态路由中的参数（例如 `/user/:id` 中的 `id`）。
- 使用非常简单，直接解构获取对应的参数值即可。

**2. useSearchParams**
- 用于获取和修改 URL 中的查询参数（Query Parameters）。
- **获取参数**：无需手动去解析 URL 字符串，底层利用了浏览器的相关 API，可以直接拿到整个 search 参数对象。
- **修改参数**：可以通过返回的 setter 函数（如 `setSearchParams`）来修改查询参数。修改后，新的参数会直接更新并反映在 URL 的 search 部分，同时组件也会重新渲染以展示最新数据。

## useNavigate 编程式导航与跳转方式 *Content-[04:31]

`useNavigate` 允许我们在组件内部通过编程的方式完成路由跳转，而不是依赖 `<Link>` 等声明式组件。

**跳转方式与类型（Navigation Function）**
`useNavigate` 返回的函数支持多种传参方式：

**1. 字符串方式**
- 直接传入目标路径的字符串。
- 示例：`navigate('/user/123')`，直接跳转到对应的路径。

**2. 对象方式（PartialPath）**
- 传入一个 `PartialPath` 接口对象，可以更精细地控制跳转细节。
- 对象属性包括：
  - `pathname`：目标路径。
  - `search`：查询参数（如 `?id=456`）。
  - `hash`：哈希值。
- 示例：`navigate({ pathname: '/user', search: '?id=456' })`。这种方式在需要动态拼接 search 参数时非常方便。

**演示场景**：在 Home 组件中添加一个按钮，点击后通过 `useNavigate` 跳转到 User 页面，并携带相应的动态参数或查询参数。

## redirect 组件外部重定向 *Content-[07:19]

`redirect` 主要用于在**组件外部**（例如在路由配置的 `loader` 函数中）进行重定向的场景。

**使用场景**：
- 在 `loader` 中模拟或发起数据请求。
- 如果获取不到所需数据，或者发生权限错误等异常情况，可以直接使用 `redirect` 将用户重定向到其他页面（如登录页或错误页）。
- 这种在数据加载阶段就进行拦截和重定向的机制，比在组件内部通过 `useEffect` 和 `useNavigate` 处理更加优雅和高效。

## useLocation 获取当前路由信息 *Content-[08:47]

`useLocation` 用于获取当前路由的完整状态信息。

**返回内容**：
该 Hook 返回一个 location 对象，包含以下关键信息：
- `key`：路由的唯一标识。
- `pathname`：当前路径。
- `search`：查询参数。
- `hash`：哈希值。
- `state`：路由跳转时携带的状态数据。

**动态更新**：
当路由信息发生变化（如通过 `useNavigate` 修改了 search 参数）后，`useLocation` 获取到的内容也会同步更新，非常适合用于需要根据当前 URL 状态来渲染 UI 的场景。

## useMatch 匹配当前路由规则 *Content-[09:47]

`useMatch` 用于判断当前 URL 是否匹配特定的路由规则，并返回匹配的详细结果对象。

**使用方法**：
- 传入一个路由规则字符串（如 `/user/:id`）。
- 如果当前路由匹配该规则，则返回一个包含匹配详情的对象；如果不匹配，则返回 `null`。

**返回结果包含**：
- `params`：匹配到的动态参数（如 `{ id: '123' }`）。
- `pathname`：当前匹配到的实际路径。
- `pathnameBase`：匹配的基础路径。
- `pattern`：匹配的规则对象。

**应用场景**：
当需要在组件内部判断当前是否处于某个特定路由，或者需要提取复杂的匹配信息时，`useMatch` 是非常强大的工具。

## 常见组件 Link 简介 *Content-[11:06]

除了上述 Hooks，React Router 还提供了许多常用的声明式组件，其中最基础的就是 `Link` 组件。
- `Link` 用于在页面中创建导航链接，实现客户端路由跳转，避免页面的整体刷新。
- 在实际开发中，通常会将 `Link` 组件与 `useNavigate` 等 Hooks 结合使用，以满足不同的跳转需求。

## AI 总结 *Content-[11:15]

本视频详细讲解了 React Router 中常用的核心 Hooks 及其应用场景：
1. **性能优化**：重点强调了 `useLoaderData` 结合 `loader` 的预加载机制，打破了传统 `useEffect` 串行请求的瓶颈，显著提升了页面加载性能。
2. **参数与状态获取**：`useParams` 和 `useSearchParams` 提供了便捷的 URL 参数读写能力，无需手动解析；`useLocation` 则提供了完整的路由状态信息。
3. **编程式导航**：`useNavigate` 支持字符串和对象两种传参方式，满足灵活的跳转需求；配合 `redirect` 可以在数据加载阶段实现高效的外部重定向。
4. **路由匹配**：`useMatch` 为复杂的路由规则判断和参数提取提供了底层支持。

掌握这些 Hooks 能够极大地提升 React 路由开发的效率与代码质量，是前端面试和实际项目中的必备技能。

---

## 文稿转写

常用的hook有哪些 比如说我们刚刚讲到的use promise 他就获获取我们当前路由的一些参数 还有我们USNAVIGATE就是进行编程式的相关导航 还有use location 获取当前的路由信息 这些都是我们非常常用的一些后感 还有use match来去匹配当前的路由 还有我们use law data 去获取我们路由加载的相关的数据 这也是可能在view当中不存在的一个特性啊 我们可以因为我们呃这个还是非常重要的 为什么非常重要 因为我们常规情形的话 我们都是这样串行的链路 我们先去加载组件 加载组件 执行组件的生命周期执行到比如说UEFFECT 等我们DOM渲染完完成以后 我们一般在UFI当中 去发起对应的一个接口的请求 去fetch一个接口 那么等我们结果回来的数据回来了以后 我们再去重新去哦 更新当前的一个组件内容 重新render对吧 我们一般这样串行的一个思路 但是呢我们有了use use loader data以后 我们就可有了我们呃这样一个嗯LODER以后 就我们路由提供的能力 我们在点跳转 点击跳转的时候 我们就会去发起对应的请求 那么发起请求之后 等页面渲染了以后 我们在UDEFINE当中 我们可以直接使用usloader data 直接就获取数据了 而无需再去等去发起对应的请求 我们这样的话是不是我们的性能会更更 我们体验会更好啊对吧 所以这也是它提供的一个呃能力 给同学推荐同学们去使用好 那么我们分别来给同学们去演示一些 重点内容啊 首先我们再看看your promise you promise就是我们刚刚的user对吧 我们先把 先把我们的路由 交换成history 交换成brother brother to 然后这样的话就OK了对吧 这样的话就OK了 我们promise就是在user对吧 user我们通过UPROMISE获取到对应的一些ID 这是都没什么问题 那么我们还有对应的 我们用search promise就查 获取对应的一些查询的一些参数 那么 那么我们可以在user当中 通过测试promise 我们也可以去修改 Doing the third promise 那么我们可以去加个button 好我们再看了一下 就如果我们当前有对应的啊 Promise 有对应的query相关内容对吧 我们这边添加对应的query 我们就能够在当前的promise当中去进行拿到 拿到我们当前promise search 我们就需要查询的相关的参数 这是查询的promise 那么这就是这样一个hook的hook的 他提供的那个能力 我们就能够直接啊 就自己无需再去解析对应的URL了 然后解析对应的呃 相关的 就直接拿到整个的一个search 也就是它会利肯定是啊 用浏览器的相关的API啊 其实就是拿到这个API啊 它提供的这些内容啊 好那么你也可以重新去设置 就是set 那么set的话它会更新到我们当前呃 后面的search premise当中 所以说这是我们such promise 它提供这样的能力好 另外呢就是我们的一个negative嗯 Use the nanavigate navigate呢就是可以让我们通过编程导航的方式 在组件中去进行一个跳转 比如说我们在MAD当中 在home当中再添加一个 跳转到我们user的这样一个内容 我们再添加一个button 能到home 这有detail a deta 二有go to 我们user123对吧 我们直接去123了对吧 所以这是我们通过编程式导航的方式 去完成对应的一些跳转的一些操作 那么我们我们navig navigate 我们看一看一下它的提供的类型 我们navigation function它提供了对应的几种跳转的方式啊 你可以提供to 那么to呢它是可以是string 也可以是我们当前ptto path 我PTOPPATH它其实是一个interface interface一个对象 你可以提供name string呃 Pass name it 提供search也定用哈 希 也就是说 我们可以有几种这种偏执导航跳转的方式 一个是我们string对吧 我当前使用这种 我们当你使用string方式 当然我们也可以提供past方 就是对象的方式去完成对应的跳转 比如PATHNAME 然后我们添加对应的search 这样的话构图456我们就会有了 对应的通过PYTHNAME的方式 以追加我们当前的search promise 然后我们这边也能渲染出对应的search promise 所以这是这样一个思路 这样思路看同学们有没有什么问题 另外呢我们也还有对应的redirect可以去呃 在我们组建外部啊 就需要进行重定向的场景 可以去使用我们redirect 好我们来看一下 当我们home的时候 模拟数据 在在此基础上可以去模拟我们当前数据的请求 我们一会儿会再来完善相关内容啊 当然我们也可以在此呃 比如说如果你获取不到 也可以去重庆向你去 可以在这里面去做相关的事情 还有还有就是我们use location Use location 就获取我们当前的路由信息 比如说我们到user的时候 用打印下当前的login相关的信息 然后这就是我们location相关的信息 我们的key 我们呃pathname search 以及我们修改一下 修改下之后呢 我们location相关信息呢就包含我们当前的设置哦 这是就能够获取到location性分析 所以这些候课也都非常的方便 还有use match is match呢就能够匹配我们当前路由 那么它会返回匹配的路由对象 匹配我们返回的这样一个路由对象 那么也是非常常用的 比如说我们可以提供在order当中 在user当中 我们利用 我们可以看到它返返回的卖匹配的一个结果 我们看到match的时候 因为我们当前的规则就是user对吧 user冒号 我们D这样的一个动态路由这个规则 那么我们看看它能够匹配到对应的内容 我们匹配到其中的promise 我们当前的参数123回到path拿到对应的path 拿到对应的匹配的规则 所以这是呃如果匹配到对应的呃 这是匹配对应的一个结果 然后通过USMATCH拿到当前那个规则 这是我们这块内容 另外一些就是一些常见的组件 我们之前我们刚刚也在使用过程中 可以给同学们去进行了一些使用 比如说我们的link呀
