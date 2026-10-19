## 目录
- [RTK Query 简介与核心优势](#rtk-query-简介与核心优势)
- [RTK Query 内部工作机制](#rtk-query-内部工作机制)
- [代码演示：基础数据查询与获取](#代码演示基础数据查询与获取)
- [核心优势深入：智能缓存机制](#核心优势深入智能缓存机制)
- [代码演示：缓存与 Mutation 变更](#代码演示缓存与-mutation-变更)
- [面试指南：RTK Query 常见问题解答](#面试指南rtk-query-常见问题解答)
- [总结与回顾](#总结与回顾)
- [AI 总结](#ai-总结)

## RTK Query 简介与核心优势 *Content-[00:01]

在日常前端开发中，与后端 API 打交道时经常面临以下痛点：
- 需要手动管理各种加载状态（如 `isLoading`, `isError`, `isSuccess`）。
- 每次发起请求都要编写一套重复的异步逻辑。
- 缓存策略复杂，数据过期处理困难。
- 组件之间的数据同步难以维护。

**RTK Query** 是 Redux Toolkit 内置的一个强大的数据获取和缓存解决方案，专门用于解决上述问题。

### 核心思想
RTK Query 的核心思想是**声明式 API**。开发者只需定义好 API 端点（如获取列表、提交文章），无需手动编写繁琐的 actions 或 selectors。它会自动生成 hooks 来处理整个请求生命周期，包括发起请求、管理缓存以及更新 Redux store 中的状态。

### 核心优势
1\. **极致简化**：大幅减少为数据获取编写的样板代码，使代码库更加清爽。
2\. **智能缓存**：自动缓存请求结果，支持后台自动更新和条件性获取，非常高效。
3\. **状态集成**：构建在 Redux Toolkit 之上，无缝集成，能够清晰追踪数据状态和请求流程。
4\. **开箱即用**：提供加载状态管理、错误处理、乐观更新（Optimistic Updates）以及轮询等高级功能。
5\. **类型支持**：为 TypeScript 提供强大的类型推导和支持。
6\. **UI 框架无关**：虽然与 Redux 紧密结合，但其核心的数据获取和缓存逻辑本身是与 UI 框架解耦的。

## RTK Query 内部工作机制 *Content-[04:00]

RTK Query 的工作机制主要分为以下三个步骤：

1\. **创建 API Slice**
通过 `createApi` 函数完成，需要定义以下关键配置：
- `reducerPath`：定义该 API slice 在 Redux store 中的路径（名称）。
- `baseQuery`：基础查询函数，通常使用 RTK 提供的 `fetchBaseQuery`，用于指定 API 的基础 URL。
- `endpoints`：定义所有 API 端点的地方，包括查询（`query`）和变更（`mutation`）。例如获取用户列表是 `query`，新增用户是 `mutation`。
- `tagTypes`：定义标签类型，这对于后续的缓存失效管理至关重要。

2\. **自动生成 Hooks**
定义好 endpoints 后，RTK Query 会自动生成对应的 React hooks，命名规范如下：
- 定义一个名为 `getPost` 的 query endpoint，会自动生成 `useGetPostQuery` hook。
- 定义一个名为 `addPost` 的 mutation endpoint，会自动生成 `useAddPostMutation` hook。

3\. **在组件中使用**
- 调用 **Query hook**：会自动发起请求，并返回一个包含 `data`, `isLoading`, `isError`, `error` 等状态的对象。
- 调用 **Mutation hook**：会返回一个触发函数（trigger function）和一个包含状态的对象。
整个过程高度自动化，无需手动 dispatch action 或编写 selectors 从 store 获取数据。

## 代码演示：基础数据查询与获取 *Content-[06:52]

在 React + Redux Toolkit 环境下，使用 RTK Query 获取 Todo List 的具体步骤：

1\. **创建 API Slice**
在 `service/api` 目录下创建 API slice。使用 `createApi` 接收配置对象：
- `reducerPath` 定义全局 state 中的名字。
- `baseQuery` 使用 `fetchBaseQuery` 指向 JSONPlaceholder 的 mock 基础 URL。
- 在 `endpoints` 中使用 `builder.query` 定义 `getTodo` 方法，返回具体路径，RTK Query 会自动将其与 base URL 拼接发送 GET 请求。

2\. **集成到 Redux Store**
- 将 `todoApi.reducerPath` 添加到 store 的 `reducer` 中。
- **关键步骤**：将 `todoApi.middleware` 添加到 store 的 `middleware` 数组中。该中间件负责管理缓存、轮询、失效等高级功能。

3\. **组件中使用**
在 `TodoList` 组件中直接调用 `useGetTodoQuery`。将返回的对象解构出 `data`（接口数据）、`isLoading`、`isFetching` 等状态。根据这些状态渲染不同的 UI，完全不需要使用 `useEffect` 发起请求或手动管理加载状态。

## 核心优势深入：智能缓存机制 *Content-[11:52]

RTK Query 的强大很大程度上归功于其内置的智能缓存机制：

1\. **自动缓存**
使用 query hook 获取数据后会自动缓存。若其他组件使用相同的 endpoint 和参数再次请求，且缓存未过期，RTK Query 会直接返回缓存数据，不发起新的网络请求，极大提升性能。

2\. **缓存标签（Cache Tags）**
通过 `providesTags` 和 `invalidatesTags` 精确控制缓存失效：
- `providesTags`：用于 query endpoint。查询成功时，给数据打上一个或多个标签。
- `invalidatesTags`：用于 mutation endpoint。变更（增删改）成功后，声明哪些标签对应的缓存应该失效。一旦标签失效，所有提供该标签的 query hook 都会重新获取数据以保证视图更新。

3\. **缓存有效期**
当最后一个订阅某缓存数据的组件卸载后，数据不会立即清除，而是保留一段时间（可配置）。有效期内再次请求可直接复用缓存。

4\. **条件性获取（`skip`）**
给 query hook 传递 `skip: true` 选项，RTK Query 会跳过本次请求。适用于依赖某些条件满足后才需要获取数据的场景。

5\. **后台静默更新策略**
- `refetchOnMountOrArgChange`：组件挂载或参数变化时重新获取（默认行为）。
- `refetchOnFocus` / `refetchOnReconnect`：窗口重新获焦或网络连接重新建立时重新获取数据，保持数据新鲜度，免去用户手动刷新。

## 代码演示：缓存与 Mutation 变更 *Content-[15:48]

通过代码演示缓存机制与 Mutation 如何协同工作：

1\. **配置 Tag 与 Endpoints**
- 定义 `tagTypes: ['Todo']`，声明使用 `Todo` 标签类型管理缓存。
- `getTodo` (query)：配置 `providesTags`，告诉 RTK Query 获取列表时，给整个列表打上 `{ type: 'Todo', id: 'LIST' }` 的标签。
- `getTodoById` (query)：根据 id 获取单个详情，并打上对应 id 的标签。
- `addTodo` (mutation)：POST 请求，用于添加新待办。核心在于配置 `invalidatesTags: [{ type: 'Todo', id: 'LIST' }]`。这意味着新增成功后，所有带有 `LIST` 标签的缓存（即列表数据）会被标记为无效，从而自动触发 `getTodo` 重新请求，实现列表自动刷新。

2\. **组件使用细节**
- `TodoList`：使用 `useGetTodoQuery` 获取列表。
- `AddTodoForm`：使用 `useAddTodoMutation`，返回触发函数 `addTodo`，在表单提交时调用。
- `TodoDetail`：使用 `useGetTodoByIdQuery` 查询单个详情。特别设置了 `skip: !id`，当 id 为空时跳过请求。

3\. **运行效果验证**
- **缓存行为**：查询 id=2 发起网络请求；再次点击查询 id=2 或 id=1 时，Network 面板无新 GET 请求，数据直接从缓存读取。
- **Mutation 刷新**：添加新 Todo 成功后，Network 面板自动触发 `todo?_limit=5` 的 GET 请求。清晰证明了 `invalidatesTags` 机制生效，实现了数据变更后的自动刷新。

## 面试指南：RTK Query 常见问题解答 *Content-[24:17]

在面试中遇到 RTK Query 相关问题时，可以参考以下结构化回答：

1\. **如何清晰表达 RTK Query 的优势？**
- 强调它是声明式数据获取库，通过自动生成 hooks 优雅处理异步状态（loading, error）和智能缓存。
- 重点提及**基于 Tag 的缓存失效机制**（`providesTags` / `invalidatesTags`），方便管理数据一致性（如列表页新增项目后自动刷新列表）。
- 总结其能显著减少样板代码，且与 Redux Toolkit 紧密集成，支持 Redux DevTools 调试。

2\. **RTK Query 与 TanStack Query (原 React Query) 的主要区别？**
- **RTK Query** 是 Redux 生态的一部分，状态最终存储在 Redux store 中。
- **TanStack Query** 是一个独立的库，有自己的缓存状态管理机制，不强制依赖 Redux。可从状态管理、API 设计、生态集成等维度进行对比。

3\. **解释 RTK Query 中的 Tag 是如何运作的？**
- 重点解释 `providesTags` 如何为查询结果标记缓存，`invalidatesTags` 如何在 mutation 成功后使特定标签失效，并触发相关 query 的自动重新获取。

4\. **如何在 RTK Query 中做乐观更新（Optimistic Updates）？**
- 乐观更新指在 mutation 实际成功返回前，先在 UI 上展示预期结果以提升体验。
- RTK Query 提供了 `onQueryStarted` 生命周期钩子，配合 `patchQueryData`（或 `updateQueryData`）API 来实现乐观更新及失败时的回滚逻辑。

5\. **RTK Query 适合与不适合的场景？**
- **适合**：已经在使用 Redux 或计划使用 Redux，且需要标准化、功能丰富的数据获取方案的中大型项目。
- **不适合**：非常简单的应用，或者团队已经有一套成熟且运行良好的自定义数据获取方案（避免过度引入）。

6\. **如何自定义 `fetchBaseQuery` 处理全局请求头或错误？**
- 通过 `prepareHeaders` 参数动态控制修改请求头（如添加认证 Token）。
- 通过包装 `fetchBaseQuery` 返回的函数，来定制全局的错误处理逻辑。

## 总结与回顾 *Content-[29:47]

- **核心概念**：RTK Query 致力于**简化与自动化**，将开发者从繁琐的数据获取和缓存管理中解放出来。
- **核心功能**：高效的数据获取、智能的缓存策略（自动缓存、标签化管理、条件获取）、无缝集成的状态管理。
- **关键掌握点**：
  - `createApi`：用于定义服务。
  - `endpoints`：定义具体的查询（query）和变更（mutation）逻辑。
  - 自动生成的 hooks：在组件中与 API 交互的主要方式。
  - `tags`：精细化控制缓存失效的利器。
- **最终收益**：显著提升开发效率，代码更加简洁易懂，内置的健壮机制有助于减少潜在的 Bug。

## AI 总结

本视频详细讲解了 Redux Toolkit 中的 RTK Query 如何简化前端数据获取与缓存逻辑。视频从日常开发的痛点出发，介绍了 RTK Query 声明式 API 的核心思想及其在减少样板代码、智能缓存、状态集成等方面的优势。通过具体的 Todo List 代码演示，直观展示了 API Slice 的创建、Store 的集成以及组件中 Hooks 的使用。重点深入剖析了基于 `providesTags` 和 `invalidatesTags` 的智能缓存失效机制，并结合实际运行效果验证了 Mutation 触发自动刷新的流程。最后，针对前端面试提供了结构化的答题思路，对比了 TanStack Query，并解答了乐观更新、适用场景及自定义请求等高频问题，是一份非常全面的 RTK Query 学习与面试指南。

---

## 文稿转写

Redux to key curry 这个工具你有用过吗 Hello 大家好 我是方格 今天呢我们来探讨 一个能够显著提升我们开发效率 告别繁琐的数据管理的利器 也就是RTKQ里 如果你还在为手动管理请求状态 然后还有编写复杂的异步逻辑或者缓存策略 而头疼 那么这一集你绝对不能错过 额那么我们在日常的开发中呢 啊会经常的和后端的API打交道 但是不知道大家有没有这样的经历啊 我们需要啊为了去获取一些手动展示 手动获取和展示数据 我们需要手动的去管理各种的加载状态 比如说啊is loading啊 is error啊 Is success 每次发起请求都要写一套差不多的异步逻辑嗯 缓存该怎么做 数据过期了应该怎么办 组件之间的数据怎么同步 那么这些问题是不是听起来很熟悉呃 也很头疼 那么好消息就是啊 redux toolkit它提供的Q里啊 就是RTKQ里就是用来帮我们解决这个问题的 好那么q redux tok curry究竟是什么呢 简单来说他是啊 Retask tokit 内置的一个强大的数据获取和缓存解决方案 他的核心思想就是声明式API 这就意味着我们只需要定义好我们的API端点 比如从哪里获取列表啊 或者说如何提交一份新的文章 而不需要去手动编写那些呃繁琐的chunks 或者是selectors Redux toky curry 它会为我们自动的生成hooks 这些hook呢 就帮助我们处理了整个请求的生命周期 包括发起请求管理管理缓存 以及啊更新redux store中的状态 他的目标就是让服务端的数据获取缓存和同步 更新逻辑变得更前所未有的简单 好在了解他是什么后呢 我们再来看看 选择REDUXTOKQ的核心优势有哪些 首先是极致极致的简化嗯 RDKQ里 它能够大幅的减少 我们为数据获取编写的样板代码 让这个带我们代码库更加的清爽了 其次呢它能够做智能缓存 这是RT k q里的一大亮点 它能够自动的缓存请求结果 并且支持后台自动更新 条件性获取数据非常的高效 再者有个状态集成的特性 由于它是构建在呃RT redux to key之上的 所以能够无缝集成redux to dv tour 让我们更清晰地追踪数据的状态和请求的流程 还有就是它开箱即用的提供了很多高级功能 比如说加载状态管理嗯 错误处理 然后还有乐观更新以及轮询等等 所以对于啊type喜欢tab screen的同学呢 他也提供了强大的类型支持 而且虽然它和reduce紧密的结合 但是它的核心的数据获取和缓存逻辑 本身是与UI框架无关的 听起来很酷炫对吧 那么我们再来了解一下啊 RDKQ里内部的工作机制啊 首先第一步呢我们需要创建一个API slice 这是通过RDK定义的一个create API 去函数去完成的 在这个函数里我们需要定义几个关键的东西 首先需要我们需要定义一个reduce pass 这个APSLI 在这个是一个aps lies在redux store中的路径 然后是需要定义一个base curry啊 它是一个基础的查询的函数 通常我们会使用RTK提供的fetch base curry啊 这个API 然后在这里我我们会指定API的基础的URL 然后第三个是end point end point就是我们需要定义所有API端点的地方 包括呃查询curious和mutations变更 比如说啊用获取用户列表 就是一个Q新增一个用户 就是一个mutation 我们还需要安可以啊定义一些tag tape 这个稍稍后我们会在讲缓存这个topics时 会详细的说它这个呃tag tape属性 它对于缓存失效是非常管理 是非常重要的 然后第二步呢一旦定义我们定义好了end points啊 RT k q里就会自动的为我们生成对应的cook 比如说啊我们定义了一个Q里呃 叫做get post的一个Q6and point 然后它就会自动的生成一个叫use get post的hook 如果定义了一个呃at ports的mutation And point 就会自动的生成一个呃use at port mutation 所以它都是啊根据这个规范命名的 然后第三步呢 我们就可以在我们的组件中去直接的使用 生成的hook了 调用这个Q里户口 它就会自动的发起请求 并且包含呃返回了一个对象 这个对象里面就包含了data 然后is loading Is error error这些状态的对象 然后呃调用mutation hook 就会返回一个触发器函数 和一个包含状态的对象 所以整个过程是非常流畅和自动化的 我们不需要手动的去派发action 也不需要手动的去编写selectors 从store中去获取数据 好理论我们刚才说了不少 接下来我们通过一段实际的代码 来直观感受一下 RTKQ里如何进行基础的数据查询和获取啊 这也这也能够帮帮助我们更好地理解 刚才提到的API slice定义和who的使用 好 在这里呢 我们已经搭建好了一个呃基础的react加REDUX to key的环境 我们的目标呢就是啊 用RDKQ里去获取一个to do list 首先呢我们要创建一个API的slides 我们在这个service service杠API文件夹下创建了一个API slice啊 然后大家看啊 这个首先啊有个create API函数 就是啊通过这个啊RRTKQ里去导出的 他在这里接受一个配置对象啊 这个配置对象里面就是我们啊 提到了刚才的一些属性 比如说这个reduce a pass 它就定义了这个slice在全局啊state中的名字 然后是base curry Base curry 就是我们用了这个fetch base curry 去指定了一个啊一个zons play 操的这个一个mock的啊基础URRL 然后在end points这里呢 我们使用了啊build点curry去定义了一个咳咳 build点curry去定义了一个嗯名为get to do的方法 然后他他的呃Q里函数就返回了一个啊 Q里函数这里就返回了一个具体的路径 这样啊 这个路径呢就和这个base ur l去拼 成了一个完整的API路径呃 同时呢我们还定了应定义了一些嗯 get to do by id啊 然后之类的查询 然后H呃 RT a q里就会自动的把这个这个路径 和这个BACYL拼起来去发get请求啊 最后呢我们还我们就把这个我们RTKQ里呃 自动生成的一些hook 比如我们在这里定义的是一个叫get to do的方法 然后在这里就是一个投峰命名的啊 Use cat get to do curi 然后这里也是you get a cat to do by cury 然后这里呃如果我们定义了一个mutation的话 额在这里他也导出相应的导出了一个mutation 嗯那么接下来我们就要把这个呃hook 把这个API slice我们定义好了 API slice去集成到我们的redux store中 呃我们主要是这么继承的嗯 在store中的配置 我们首先把这个to do API点reduce pass啊 这个字段添加到了这个reducer里面啊 然后并且非常重要的一点就是呃 把这个MIDWELL 这个在这MIDWELL这里去添加了一个啊 to do API点mid well 这个中间件就负责负责管理啊 缓存以及轮询失效这些高级的功能 好在API和store都配置好后 我们看一下呃 我们如何在组件中去使用它 嗯在这个to do list里面呢 我们啊直接调用了这个use get to do curry这个方法啊 这个hook他就返直接的返回了一个对象 我们啊把这个对象解构之后呢 呃把它结构出了一个data 就是一个接口返回的数据 然后还有LO状态以及啊loading和fashion的状态啊 啊其实还可以有一个啊low loading啊 fection infection和一个fetch的函数REFETCH 所以我们根可以根据这些状态去渲染不同的UI 大家可以看到我们哦 完全不用去且uc effect来发起请求 也不用手动的管理这些加载的状态 嗯RTKQ里这个工具就自动的帮我们做好了 是不是非常的简洁 好通过刚才的演示呢 相信大家对RT k q旅如何简化基础数据的获取 有了一个直观的认识 那么接下来呢 我们深入探讨它的另外一个核心优势 也就是缓存啊 RT k q里之所以强大呢 很大程度归功于它内置的智能缓存机制 呃那么它是如何简化我们的缓存逻辑呢 首先有个自动缓存的特性 当你使用啊curry hook去获取数据的时候呢 啊 RTKQ里就会自动的把成功获取的数据 缓存起来 如果之后有其他的组件使用相同的end point 和相同的参数 再次请再次请求数据 并且缓存数据尚未过期 那么RTKQ里就会直接从缓存中去返回数据 而不会去发起新的网络请求 这样就能极大的提升应用的性能和应用体验 用户体验 然后就是呃缓存tag缓存标签 这就是这是一个非常强大的概念 通过啊 and points去在里面去定义provide tag和invalid tag 我们就可以精确的控制缓存的失效 首先provide taprovide tag 这个属性呢就是用在QE类型的end point 当一个呃一个Q里 一个查询成功获取数据的时候呢 你就可以用这个provide tax 给这些数据打一个或者多个的标签 然后in value tx用在mutation类型的一个end point 当一个mutation比如说添加嗯 删除或者修改成功执行以后呢 你可你就可以用invalid text来声明 哪些标签对应的缓存数据应该失效 一旦某个标签的缓存失效了 所有提供呃该标签的curry hook 都就会重新的获取数据 来保证视图的更新 然后呃 RT k q铝还允许我们配置缓存的有效期啊 嗯这就意味着就是当最后一个订阅 最后一个订阅了某个缓存数据的组件卸载后 这些数据是不会立即从缓存中清除的 而是会保留一段时间 如果在有效期内又有数据需要 又有组件需要去获取这些数据 就可以直接从缓存中获取嗯 还有一个条件性获取叫skip 我们可以给这个curry hook传递一个skip skip冒号true的一个选项 这样的话呃red curry就会跳过这次请求 在这在某些依赖条件满足后 才会需要获取数据的场景下去 是非常有用的一个属性嗯 然后最后呃react qui Redux Redux to key qui 还去还会支持多种的呃后台静默更新策略 比如说这两个属性 就refetch amount or argue on change 这是在组件挂载或者参数变化时重新获取 这是一个默认行为 以及呃refetch on focus reflection on connect 就表表示网络连接重新重新连接时 它会重新获取数据 这些都能保证我们保让我们保持数据的新鲜度 不用让用户去做手动刷新的操作 好在理解了缓存的一些基本原理 特别是一些tag的概念后 我们再次回到我们的代码编辑器啊 通过一些实际的例子来看看哦 这个RTKQ里缓存是如何工作的 以及如何通过mutation来变更数据 并且自动的更新缓存 好我们先来看最核心的部分啊 啊这里有几个关键点 首先我们在这里去定义了一个tag type啊 去声明我们用to do这个标签类型来管理 待办事项的啊一个缓存 然后在at point的get to do里呢 我们呃就定义了一个provide tax啊 这protect provide text就告诉了RTAQ里 当获取到这个呃待办事项列表的时候呢 你要给整个的列表打上一个啊 type是to do id是list的标签 然后第三点我们新增了一个呃 get to do by id的查询了 它会根据这个啊id来自动的获取 单个的待办事项 并且在啊通过provide tag去打上对应的标签 然后这里还有个at to do的mutation 它是一个post请求啊 这呃用在给服务端去 向服务端去添加一个新的待办事项 它最核心的点在于这个invalid tx 这就意味着就是 当这我们只要新增了一个待办事项 调用了这个as to do成操作成功之后呢 所有带有啊type为to do id so list的标签缓存数据都会被标记成无效 所以当这个添加操作成功后 get to do就会啊gas to do就会自动的被触发啊 重新重发 从而从而获取最新的待办事项列表 这也就是我们实现列表自动刷新的秘密所在啊 啊然后之后的流程其实和之前一样 就是把这个to do API的reducer和这个mid well 添加到这个reduce store里 然后我们再来看看这个前端组件 是如何使用这个API的 首先来看这个to do list 这里有个这个hook 我们之前也介绍了 就是用来获取代办实现列表的 然后到了这个ADD to do phone 在在这里的话嗯我们看一下 我们又使用了这个use ADD to do的这个mutation啊 它会返回一个触发函数叫ADD to do 然后在嗯这个handle submit里面的啊 我们调用这个ADD to do 我们调用这个ADD to do 并且传入了新的一个待办事项标题啊 然后呃它就实现了一个ADD to do的触发嘛 然后为了呃展咳 然后这里这个组件适用于我们去展示一个 缓存行为的 首先啊我们使用这个use啊 get to do q里by id 这里我们就根据id去查询 单个待办事项的查额详情了 需要注意的就是 我们这里还特特还设置了skip选项啊 在id为空时 我们会跳过请求好代码部分就到这 我们先啊我们接下来看看啊 实际的例子 实际的运行的效果好的 大家可以看到在现在页面上有三个主要区域 一个是添加呃待办事项列表的 然后这个是这个区域是获取额 单个待办事项详情 然后这个是展示呃代办代办事项列表的 首先我们来观察一下缓存行为呃 我们先输入一个id叫二 然后他在这里做了一个网络请求 这里id这里会调用一个杠to do4杠二啊 然后在这个区域也会展示to do2为to do id为二的详情 然后我们额再次的去点击这个按钮嗯 大家可以发现大家可以发现呃 注意观察这个啊 网络d EV tour 你会发现这次没有新的get请求啊 所以呃RTKQ里就会自动的从缓存中返回了 数据 输入一其实也是一样的 他不会去做网络请求 因为刚才我们已经呃调用了一这个API to do是一个这个API 所以这就是RDKQ里的 强大的自动缓存的行为 他就会它会智能地判断数据是否已经被获取 并且有效 从而避免不必要的网络请求 然后接下来我们演示一下啊 mutation导致的缓存失效与自动刷新 我们首先整体的刷新列表 我们看一下这个fetch啊 这里有个to do limit5 他就是一个获取列表的一个API 然后然后我们关注一下呃 我们在这里去输入一个标题二三 然后我点击ADD to do嗯 在ADD to do里呢 呃我们先首先发了个请求 就是ADD 啊刚才网络有点慢 现在啊土豆丝已经有返回了 然后呢呃你会发现 当我们呃调用成功这个to do s之后呢 它会啊又一次的去调用这个呃杠limit to5 因为它呃我们这是我们的一个业务逻辑啊 就是在这个添加完呃待办事项列表之后呢 这个列表数据要重新刷新 所以额所以你会看到你会发现哦 我们通过网络工具请求看到 清晰的看到这个get的请求被重新的处罚了 这就证明了啊RT k q里的一个invalid tag的机制 他是正常工作的 因为我们每次哦获取数据之后呢 他会给这些列表项去打一个tag 然后再啊重新请求时啊 因为他invalid tag的机制 所以导致这个tag失效呃 导致RTAQ里去重新的出发请求 所以通过这个更清晰的演示啊 大家可以看到RTKQ里 如何智能的处理数据的请求和缓存 首先它会自动的缓存数据去避免重复的请求 同时呢通过mutation的invalid tag和QI的providence tag 去实现了数据变更后 相关的数据自动的失效和刷新 这样就极大地提升了我们开发者的效率 和用户的体验 好在理解了我们RTKQ里的核心功能之后呢 如果在面试中你被问到类似的问题 我们应该如何清晰地表达它的优势呢 有几个关键点啊 首先你可以说RT a q旅是一个功能强大的声明 是额数据获取库 它极大地简化了前端应用和服务端之间的 数据交互方式 它最核心的优势之一就是通过自动生成的hook 帮我们优雅地处理了异步请求的加载状态 比如说is loading啊 is error啊 错误处理 以及非常重要的就是啊 智能缓存和自动获取组逻辑 这样这就意味着我们不需要再为每个请求 去手动的编写大量的样板代码嗯 特别值得一提的就是 它是基于text的失效缓存失效机制 通过在API定端点时额定义 在API端点时配置provided tag和invalid tag 我们就可以很方便的去管理数据的一致性啊 比如说用户在一个列表项 列表页去添加了一个新的项目 这就是一个mutation操作 RTKQ里 就可以自动的让这个列表的缓存失效 并且重新获取最新的数据 保持试图的实时更新 总的来说 RTKQ里它显著的减少了样板代码 就是呃样买代码 指的是减少了数据获取和状态管理 相关的样板代码 让开发者更加专注于业务逻辑的实现 而不是陷入在数据流管理的细节中 而且呢它与r redux to kit是紧密集成的 我们可以充分利用啊 redux d v tour去进行状态追踪和调试 这为我们开发的维开发和维护 带来了极大的便利 用这样的结构化重突出重点的方式来回答 能够更好地展示你对RTKQ里的深度理解 嗯那么除了问RTKQ里的优势之外 面试官可能还会问一些具体的问题 我们来看一下 选第一个RT啊 redux curry啊 与RTAQ里和react qui 现在现在我们叫它TENSQ里啊的区 主要区别是什么 这是个非常经典的问题啊 你需要思考他们的设计哲学 比如说嗯RTAQ里是REDUX生态的一部分 它的状态最终是存储在redux store中的 而啊TENSSECURITY是一个独立的库 它有自己的管理缓存状态 它不强制依赖REDUX 你可以从呃状态管理API设计 生态集成这些方面去比较 然后第二个是解释啊 RTAQ里中的tag是如何运作的 呃我们刚刚才在代码演示中已经详细接触过了 你需要重点关注的就是provided tag和invalid tag 这两个属性你需要解释啊 provided tag它是如何标记缓存数据的 然后invalid date text是如何在mutation成功后 使得特定的标签缓存失效的 以及如何啊 这如何触发相关的Q里的自动获取 然后第三个是额 如何在RTAQ里中做乐观更新啊 乐观更新指的就是在mutation请求实际成功返回前 就在UI上展示预期的结果 以提升用户体验嗯 RTAQ里提供了嗯on curity start 然后还有patch que data这些这些API啊 来帮助我们实现乐观更新和失败时的回滚逻辑 这是一个进阶的话题 可以如果感兴趣的话 可以深入研究一下 然后额RTAQ里适合哪些场景 不适合哪些场景 首先呢呃我们要理解是没有万金油的 RTAQ里是非常适合那些已经在使用REDUX 或者计划使用REDUX进行状态管理 并且需要一个标准化的功能 丰富的数据获取方案的项目 对于简单的应用或者团队 已经有了一套比较成熟而且良好的运行 良好的自定义数据获取方案呃 引入RTAQ里就是可能是不必要的 然后第五个如何自定义fetch base curry 来处理全局的请求头或者错误嗯 fish base curry这个属性呢 就允许我们通过嗯prepare header 这样的参数去来控制动态的控制修改请求头 比如说添加一个认证的token 或者我们可以通过包装啊 他的方式来啊定制我们的全局的错误处理 所以对于这些问题你也可以有所准备啊 能够让你在面试时更加从容好 我们额关于RTKQ里的内容 我们今天就讨论在到这里了 我们快速回顾一下核心的要点 首先呢 RTAQ里的核心概念就是简化和自动化 他致力于将我们从繁琐的数据获取 和缓存管理中解放出来 它的核心功能就包括高效的数据获取 以及智能的缓存策略 包括自动缓存啊啊标签化管理 条件获取等 以及无缝集成的状态管理 所以要理解R和使用RTAQ旅 你需要掌握几个关键概念啊 一个create API是用来定义你的服务的 and points定义了具体的查询和变更逻辑 然后自动生成的户口是啊 我们在组件中与API交互的主要方式还有tag tag就是更用来更精细化的控制缓存的利器 所以最终使用RTKQI给我们带来的收益 主要就是显著地提升了开发效率 让我们的代码更加简洁易懂 同时呢由于它内置的健壮机制 也帮助我们减少了潜在的bug啊 非常感谢大家的观看啊 希望通过今天的讲解 你能对 RTAQ里如何简化数据获取和缓存逻辑 有一个更清晰的认知 并且能在你的项目或者面试中 自信地运用这些知识 好啊 我今天的讲解就到此结束了 我是方格 我们下期再见
