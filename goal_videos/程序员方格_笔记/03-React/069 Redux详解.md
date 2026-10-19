- Redux 核心概念与特性
- Redux 状态流转机制
- 原生 Redux 基础使用
- Redux 与 React 18 的底层对接
- Redux Toolkit (RTK) 简化开发
- 前端状态管理方案总结与选型
- AI 总结

## Redux 核心概念与特性 *Content-[00:00]

Redux 是一个非常优秀的状态管理库，主要提供以下核心概念和特性：

- **单向数据流**：Redux 提供了严格的单向数据流概念，使得状态的变化更加可预测。
- **集中状态管理**：将全局状态集中管理，避免状态分散在各个组件中难以维护。
- **可预测性**：通过纯函数来修改状态，确保状态更新的可预测性。
- **中间件支持**：提供中间件机制（如 `redux-thunk`、`redux-saga`）来支撑异步操作。
- **繁荣的生态**：经过多年的发展，Redux 的生态系统非常繁荣。

### 核心原则
1\. **纯函数 (Pure Function)**：Redux 的 Reducer 必须是纯函数。即相同的输入参数永远返回相同的结果，且没有任何副作用。不能直接修改当前状态，而是返回一个新的状态对象。
2\. **单一数据源 (Single Source of Truth)**：全局的状态树 (Store) 是唯一的，所有状态都集中存储在这里。
3\. **State 是只读的 (Immutable)**：State 不能被直接修改。要更新状态，必须触发 Action，通过 Reducer 返回一个新的 State 对象。这体现了 Immutable（不可变性）的思想。

## Redux 状态流转机制 *Content-[02:18]

Redux 的状态流转是一个清晰的单向数据流过程，具体步骤如下：

1\. **View (视图层)**：当视图需要更新状态时，会 dispatch（派发）一个 Action。
2\. **Dispatch Action**：通过 `dispatch` 方法将 Action 发送到 Store。
3\. **Reducer (纯函数)**：Store 接收到 Action 后，会调用 Reducer 函数。Reducer 接收当前的 State 和 Action，计算并返回一个新的 State。
4\. **Store 更新**：新的 State 会更新到 Store 中。
5\. **订阅发布机制 (Notify)**：由于 Store 内部采用了发布-订阅模式，当 State 发生变化（返回新对象）时，Store 会通知所有订阅了该状态的组件。
6\. **View 重新渲染**：组件接收到通知后，触发对应的更新机制，重新渲染视图。

## 原生 Redux 基础使用 *Content-[04:00]

在不使用 Redux Toolkit 的原生 Redux 版本中，基本使用流程如下：

- **定义初始状态**：定义 `initialState`。
- **定义 Reducer**：创建一个纯函数，接收 `state` 和 `action` 作为参数，根据 action 的类型返回新的 state。
- **创建 Store**：使用 `createStore` 创建 store。Store 对象核心包含三个方法：
  - `getState()`：获取最新的 state。
  - `subscribe()`：订阅状态变化，当 state 改变时触发回调函数。
  - `dispatch()`：触发 action，用于更新状态。

### 在 React 组件中使用
- **Provider**：在顶层组件（如 `App`）中使用 `<Provider store={store}>` 将 store 传递给子组件。
- **useSelector**：在子组件中使用 `useSelector` 获取 store 中的特定状态（如 `count` 值）。
- **useDispatch**：使用 `useDispatch` 获取 `dispatch` 方法，用于触发 action 更新状态。

*注：在 Redux 源码中，会结合函数式编程思想（如 `compose` 函数组合）来实现中间件的组合与状态管理。*

## Redux 与 React 18 的底层对接 *Content-[06:45]

理解 Redux 状态变化如何对接到 React 的渲染机制是面试和深入理解的重点。

- **useSyncExternalStore**：React 18 引入了 `useSyncExternalStore` 这个 Hook，专门用于将外部状态管理库（如 Redux、MobX）与 React 的渲染机制对接。
- **工作原理**：Redux 内部使用了这个 Hook。它将 Redux 提供的 `subscribe`（订阅方法）和 `getSnapshot`（获取当前状态快照的方法）传递给 `useSyncExternalStore`。
- **触发更新**：当外部 Store 的状态发生变化时，会通过 `subscribe` 通知 React，React 随后会重新获取最新的 snapshot 并触发组件的重新渲染。

## Redux Toolkit (RTK) 简化开发 *Content-[08:12]

原生 Redux 存在样板代码多、异步处理不够友好等问题。Redux Toolkit (RTK) 作为官方推荐的工具，极大简化了 Redux 的使用。

### RTK 的核心优势
- **简化 API**：减少了大量的样板代码。
- **内置 Immer**：内部集成了 Immer 库，允许在 Reducer 中直接“修改”状态（实际上是 Immer 在底层帮你创建了不可变的新对象），使代码更符合直觉。

### 核心 API：createSlice
`createSlice` 是 RTK 中最核心的方法，用于创建一个状态切片（Slice），它将 State 和 Reducer 结合在一起。
- **参数配置**：包含 `name`（切片名称）、`initialState`（初始状态）、`reducers`（修改状态的方法集合）。
- **自动导出**：`createSlice` 会自动生成并导出对应的 `actions`（如 `increment`, `decrement`）和 `reducer`。

### 配置 Store 与使用
- **configureStore**：使用 `configureStore` 配置全局 Store，将各个 Slice 的 reducer 传入（如 `counter: counterSlice.reducer`）。
- **组件使用**：与原生 Redux 类似，在组件中通过 `useSelector` 获取状态，通过 `useDispatch` 派发 actions。

### 多 Slice 示例演示
在实际工程中，通常会根据业务模块创建多个 Slice：
- **Counter Slice**：管理计数器状态（加减操作）。
- **User Slice**：管理用户信息状态。
- **Todo Slice**：管理待办事项列表。包含 `addTodo`、`removeTodo` 等 action。在组件中通过 `useSelector` 获取 `items` 数组进行遍历渲染，并通过输入框和 `dispatch` 实现添加和删除功能。

## 前端状态管理方案总结与选型 *Content-[14:50]

在 React 开发中，需要根据项目的规模和复杂度选择合适的状态管理方案：

1\. **useState**：适用于简单的、组件内部的局部状态管理。
2\. **useReducer**：适用于组件内部较为复杂的状态逻辑管理。
3\. **useContext**：适用于跨组件的简单通信，避免 Props Drilling（属性透传）。
4\. **Redux**：适用于大型应用，负责全局的、复杂的状态管理。
5\. **Redux Toolkit (RTK)**：用于简化 Redux 的开发体验，是目前使用 Redux 的首选方案。

### 渐进式演进建议
在项目初期，可能无法准确预估整体复杂度。建议采用渐进式演进：
- 从 `useState` 开始，当状态逻辑变复杂时，平滑过渡到 `useReducer`（两者代码结构相似）。
- 当需要全局状态管理时，引入 Redux/RTK。由于 RTK 的 `createSlice` 与 `useReducer` 思想类似，迁移成本较低，只需将 state 转换为 slice，并导出相应的 actions 即可。

### 其他解决方案
除了上述方案，前端社区还有许多优秀的状态管理库，例如 **Zustand**（转录中识别为 Stand），它以轻量、简洁的 API 受到广泛欢迎，也是大型项目状态管理的优秀备选方案。

## AI 总结

本视频详细讲解了前端面试高频考点 Redux 及其生态。首先介绍了 Redux 的核心概念（单向数据流、单一数据源、纯函数、不可变性）及状态流转机制。接着演示了原生 Redux 的基础用法，并深入剖析了 React 18 中 `useSyncExternalStore` 如何与 Redux 底层对接。随后，重点讲解了 Redux Toolkit (RTK) 如何通过 `createSlice` 和内置 Immer 大幅简化样板代码，并展示了多 Slice 的实际应用。最后，对 React 状态管理方案（useState、useReducer、useContext、Redux/RTK）进行了横向对比与选型建议，强调应根据项目复杂度渐进式选择，并提及了 Zustand 等其他优秀方案。整体内容逻辑清晰，是掌握前端全局状态管理的绝佳指南。

---

## 文稿转写

这是我们这样一个特性 那么接下来我们看看第五个就是通过relax 进行我们集中的状态管理 那么REDUX呢它是非常棒的 这样状点状态管理库啊 提供了单向数据流这样的概念 就单项数有这样的概念 那么我们集中的去进行装的管理 并且可以预测我们当初的更新 还有一些中间件的思路去支支撑 我们当前异步的相关操作 并且这么多年他状态它生态库是非常的繁荣的 那么我们可以啊 他其实跟我们刚上述讲的啊 reducer其实跟我 我们其实也有类似我们的REDUX相关的概念 我们都需要纯函数来去进行修改 当前的一个状态 而不是直接对我们当前的状态去进行修改 那么什么是纯函数呢 这同学们应该都清楚 就我们函函数的调用的参数相同 那么返回的结果是永远是相同的 这样的话我们才是可信的 没有任何副作用的对吧 这样的一个思路呢 我们才能够更好的去维护当前的一个状态好 那么我们看看啊 我们看看它主要有一个特性 一个是单一数据源 单一的数据源 我们全局的store来去重新去除啊 这是跟我们我们是action呢描述当前状态变化 Dispution reduce呢纯函数修改当前action 以及通过dispatch去触发当前action状态 还有一些他提供的一些后客 比如中间件中间处理异步的方式 我们通过redux trunk啊 redux solar来去我们进行中间件的一个处理 还有呢我们现在都是使用RDK 就REDUXTOGET来去简化我们当前relax嗯 REDUX使用 那么我们针对这个store呢 它是只读的 我们state是只读的 不能够直接去修改 我们需要返回一个新的对象才能够修改 因为我们当前在right内部 它使用嗯 我们当前JS使用的是单一 我们单向数据流 并且是IMMORTABLE的对吧 我们只能够修改 只能够返回一个新的对象来去进行 让我们已经发生变化来去更新 当前触发了我们组建的一个更新 所以是这样的一个思路 在我们呃简单画个图啊 简单画一个它的 它的状态流转 首先我们分为这么几部分啊 首先我们的view就我们试图 我们试图需要修更新状态变化呢 我们就需要通过dispatch一个我们这这个action Dispatch 我们这样一个action以后啊 我们通过reducer调用reducer函数 这reducer呢它会返回一个新的这样一个state对吧 返回新的state 比如去更改我们store里面的值 我们store里面发生变化 因为我们是整体是一个订阅发布 那么我们这边哦返回了一个新的state 那么新的state是一个新的一个对象 那么这个对象呢我们就会触发重新去嗯 通过它会通知 我们通过通过notify去通知我们当前view 去触发对应的一个更新机制 所以整体流程是这样 是这样的一个单向数据流 整体来讲是比较简单的比喻 并且易于易于理解的哦 那么我们看看我们的demo 这是我们使用如talk it 那么先先不使用我们talk it版本啊 我们先使用就是crystal e redux版本 先去定义我们当前初始状态 我们initial state定义初始状态 那么接下来我们需要定义reduce函数 它是一个纯函数 接触state解除action对吧 其实跟我们上述的reduce reduce use uer比较相似的对吧 同学们这理解起来就比较的 应该都是比较好理解了 我们就需要创建redux store 我们需要订阅当前状态的变化 所以我们当前cris store分为这 其实核心它返回就是一个这个store里面 一个是包含subscribe 它包含这么几个 包含着store里面包含这么几个内容 一个是SUPERVIBE去订阅我们当前的变化 那么我们通过get get state去获取最新的state 如果我们state里面发生变化 它会触发到我们这个函回调当中 还有我们dispatch 所以它会提供这三个方法 Get state Subscribe dispatch Dispatch 好这就是一个简单的一个使用 在我们组件中如何去使用呢 就可以通过这种方式去进行使用 好在我们组件当中a p p view当中 我们provider它提供对应的store对吧 提供对应的store 那么store呢里面什么内容呢 里面其实就是我们这几个get as state呀 dispatch啊 subscribe啊 这等等这几个方法 那么哦去传给传递给我们当前子组件 我们counter组件呢通过我们用select来去 通过select count获取到我们当前的count值 就是康康的值 以及我们通过USDISPATCH获取 我们更新dispatch的一个方法 那么我们会在源码课程中会给他们去讲解 或者手写一个我们当前的relax 看看它具体是如何去实现的 以及我们它里面的相关的 我们的dispatch相关的reducer 还有dispatch 还有它的一个冲击键 我们都需要去结合着我们之前函数 编程相关的一些思想 比如说compose我们函数组合的这一方法 去组合我们当前的一个中间件等等 这都是它在源码当中体现的相关的一些能力 那么我们这边拿到count 拿到dispatch 就可以去进行渲染以及去更新当前的方法 所以这是我们REDUX提供的一个内容好 那么接下来我们看看 就是我们需要重点去知道我们relax变化 怎么去对接到我们director 这一点同学们一定要格外清楚 它着重其实是使用我们在内部啊 其实使用我们 You you think external store 那么也就是我们需要通知react去进行 它是react react18引入这样一个hook 用于我们外部状态 跟比如说我们relax mob 他去跟我们react 通过uthink external store 也就是我们react or 它是作为它其中的一个订阅 因为然后我们会把更新的方法传传递给他 比如引入我们u u is single external store 我们假设有一个外部的这样一个状态 那么这其实就是我们当前relax提供的subscribe Get 我们snapshot等等这样一个store提供的相关的方法 通过它获取我们当前的状态 然后去渲染 如果这通知我们当前定义者发生变化 它会通知到我们这里 我们这里就会重新去进行一个渲染 所以这个这个钩子同学们一定要清楚 一定要清楚好 那么我们接下来看看redux ticket 它是简化了我们relax的使用 相信使用redux relax的同学应该会发现 他那个样板代码还是非相对来讲比较复杂的 要写比较多的样板代码对吧 那么以及我们异步的一些处理呀等等 它们使用起来其实并没有特别的友好 那么我们RTK就是tx tit 就是简化了我们相关的一些API 能够让我们的使用起来会更加的方便 并且它支持了内部集成了我们email 就是进行状态不可变相关的更新 也就是我们可以更通过直接去操作 修改我们当前的数据去触发它的更新 因为内部他已经把我们当前音引入了英ma 那么就会他利用email重新去创建一个新的对象 帮我们去包了这么这么一层 那么我们就呃它提供了create slice这样的方法 什么是create lice呢 create slice就是用来去创建 我们当前的一个对一个对象创建一个状态 那么它里面去包含 比如说我们可以great size 我们当前的里面包含我们一个状态值 我们当前呃reducer的一些方法 所以说这就是类似我们store 把我们的呃state和reducer两者去进行一个结合 我们相当于分状态分片 我们可以创建不同的store slice 比如说我们创建一个counter slice 我们有当前counter 提供slice name以及当前初始化的值 以及修改 当它这个counter的方法有哪些 比如说所以我们需要在看reducer当中去定义 我们crement decrement好 这样的话它会导出我们的 比如说action呢 就通过呃counter slice去进行一个导出 导出我们当前action其实就是我们当前呃increment啊 decrement这两个方法 那么我们去创建redux store 通过配置把我们当前Ctrl slice好进行 通过放入到我们counter啊 control呃 config graph里面的store里面去进行一个配置 它会返回我们当前的store 我们如何使用呢 在我们count当中 通过USELECT去获取当前的状态 通过dispatch获取当前的内容 好通过这种方式就能够 因为就能够更主要是我们slice里面它呃 创建这个slice以后 它是比如说对应的action 对应的dinner store都是由它来去衍生出来的 由它由这个来去衍生出来的 所以说我们简化了整体的这样一个样本代码 好核心就great less 我们可以继续 创建user slice 这是我们创建的useless 以user对应的呃store UER的对应的action 我们user的相关的使用 Is the perfume 所以不同的状态 我们都是通过创建自己的slice 比如我们继续 我们创建一个呃像 我们创建一个像hobby 嗯像我们继续创建slice啊 我们看看还有什么slice 给同学们去增加一下它的一个复杂度 我们可以创建一个像hobby 或者是我们呃 课程的slice 那么在这个课程slice呢 或者说是我们创建一个to do slice 就我们to do包含 比如说在我们数组里面去添加to do remove to do 对吧 那么我们创建反导出我们当前action 然后导出我们当前store 那么创建我们当前组件 在组件中使用我们提供的 我们to do list 好这样的话在我们这个to do list当中 我们获取当前的items Dispatch 以及我们new to do 那么我们便利items遍历渲染当前to do 那么每个都有 比如despite是一个remove to do remove to do呢 就是我们这边导出的呃 他的action 还有我们set new to do 然后啊通过去添加一个安全to do 然后之后呢我们把当前的input框给给清空掉 所以这样这样一个slice 所以我们通过这样一个demo 就演示了不同的slice 它整体一个内容 有同学们到时候再写我们当前的整体的一个呃 工程的内容时候 我们其实就创建不同的size 不能nice 然后无需去创建action呢 无需创建对应的呃store呀 我们只需要通过哦 通过我们counter 通过对应的slice去导出 所以它整体来讲还是相比我们relax 能够哦轻松的很多好 这是我们对应的REDUX相呃 我们的URERTK相关内容 我们来总结一下 我们总结一下 首先就是我们通过your state来去 适用于我们比较简单的一个组件的一个状态啊 还有呢我们通过有就dual 就是适用复杂的一些状态管理 那么我们通过UCONTEST去适合 我们跨组件相关的一些通信 我们通过or redux来呢 他主要是负责一些大型的应用 进行传局的状态管理 还我们通过ELITOKT去简化 当前我们relax相关的使用对吧 大相关使用 所以说这是我们 我们需要根据我们当前的使用的规模啊 还有我们当前工程的一些复杂度啊 来选择比较适合的一些方案 那么可能前期你不一定能够哦 知道整体的项目复杂度 那么针对这种情况下 其实我们也可以去一步一步去演进 因为这样的话整体对我们代码的一个改动 其实还还好对吧还好 因为我们可以看到像我们U1开始使用UUSER 跟我们后续的relax 它们都是非常相似的 整体的一个代码结构对吧 那么以及后续如果你基于去使用IDK的方案 我们只需要把之前的USR呃 它定义的state等等 你转换成对自己的slice 然后我们的相关action啊 都由我们CONSLICE去进行一个导出 其实整体来讲改变现在还OK好 这是我们讲说这几个方案 那么接下来我们再看看一些呃 其他的一些解决方案 比如说如此 Stand
