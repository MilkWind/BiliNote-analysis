## 目录
- useSelector 的作用与原理
- React 渲染流程
- AI 总结

## useSelector 的作用与原理 *Content-[00:00]

### 1\. 核心作用与背景
- **主要作用**：`useSelector` 是 `react-redux` 库中的一个 Hook，主要用于从 Redux store 中读取某一段特定的数据。
- **React 项目核心三库**：在实际的 React 项目中，通常需要配合以下三个核心库使用：
  - **React**：核心 UI 渲染库。
  - **Redux**：负责全局状态管理。
  - **react-redux**：负责将 React 与 Redux 进行状态关联，`useSelector` 即属于此库。

### 2\. useSelector 的核心原理
- **数据获取与监听**：
  - 通过传入的 `selector` 函数获取所需的数据。
  - 向 store 中通过 `subscribe` 方法注册回调函数，以监听状态变化。
- **更新触发机制**：
  - 每次发起 action 时，都会重新调用 `selector` 函数。
  - 将 `selector` 函数的新返回值与老值进行**引用比较**。
  - 如果返回值的引用发生变化（不一样），则会触发组件的重新渲染。
- **底层更新原理**：
  - 底层最核心的原理是使用了 React 内部的 `useReducer`。
  - 通过调用 `useReducer` 返回的第二个参数（即触发渲染的方法），直接调用该方法来实现页面的强制更新。

## React 渲染流程 *Content-[01:42]

### 1\. 运行主干逻辑
React 的运行主干逻辑主要包含以下三个步骤：
- **输入**：将每一次的状态更新（如新增、删除、修改节点，或调用 `setState`）视为一次更新需求。
- **注册任务**：React 新版本基于任务调度机制。当 React Reconciler 收到更新需求后，会在调度中心（Scheduler）注册一个新的任务（Task），将更新需求转换为调度任务。
- **执行任务**：调度中心（Scheduler）通过任务调度循环来执行注册的任务，输入与调度两者相辅相成。

### 2\. 任务执行的两阶段模型
执行任务主要分为两个核心阶段：
- **Render 阶段**：构造 Fiber 树（将虚拟 DOM 转化为 Fiber 树）。
- **Commit 阶段**：将构造好的 Fiber 树渲染到最终页面上，更新 DOM 并执行副作用逻辑。

### 3\. Render 阶段（可中断）
- **核心特点**：Render 阶段是**可以打断的**，这是 Fiber 架构的核心优势。
- **调度特性**：具有优先级机制，且根据中断和恢复的情况，Render 阶段有可能被执行多次。

### 4\. Commit 阶段（同步执行）
- **核心特点**：Commit 阶段是**同步执行**的，内部的三个小阶段依次顺序执行，不可打断。
- **三个子阶段**：
  - **Before Mutation**：DOM 更新前的阶段。
  - **Mutation**：在此阶段更新真实的 DOM。
  - **Layout**：DOM 更新后的阶段。

### 5\. Hooks 的执行时机
- **useLayoutEffect**：在 Commit 阶段的 **Layout** 子阶段执行。由于 Commit 是同步的，因此它的执行一定是在页面真实 DOM 更新之后同步执行。
- **useEffect**：属于**异步执行**（宏任务）。虽然它的调度调用发生在页面更新之前，但其实际执行是在页面更新之后异步完成的。

## AI 总结

本视频主要讲解了 React 生态中 `useSelector` 的底层原理以及 React 核心的渲染流程。
1. **useSelector 原理**：作为 `react-redux` 的核心 Hook，它通过 `selector` 函数提取数据，并利用 `subscribe` 监听 store 变化。当 action 触发时，通过引用比较判断是否需要更新，底层依赖 `useReducer` 的 dispatch 方法强制触发组件渲染。
2. **React 渲染流程**：React 的更新分为输入、注册任务、执行任务三步。执行任务分为 **Render** 和 **Commit** 两个阶段。Render 阶段负责构建 Fiber 树，支持中断和优先级调度；Commit 阶段负责同步更新 DOM 并执行副作用。
3. **Hooks 时机**：明确了 `useLayoutEffect` 在 Commit 的 Layout 阶段同步执行（DOM 更新后），而 `useEffect` 作为宏任务在页面更新后异步执行。掌握这些底层机制对于应对大厂前端面试及优化 React 性能至关重要。

---

## 文稿转写

好OK接下来我们来看啊 react中use是select的作用啊 啊它是react杠REDUX库中的一个方法 从我们redux store中去读取某一段数据 好我们来看一下USELECT它的一个简单原理啊 这个面试的时候可能会问到啊 啊它实际上是react杠REDUX中的一个hook对吧 那实际上我们在做react项目的时候 一般呢最核心需要这是啊 需要用到这三个库对吧 一个react 一个REDUX对吧 REDUX是状态管理 react杠REDUX是进行状态关联的 那这个use是select 它就属于react杠REDUX这个库啊 好OK那实际上啊它的原理通过select的函数对吧 得到我们需要的数据 然后向使store中通过subscribe去注册回调 所以每次当我们去发起action的时候啊 那我们都会去重新调用select函数 然后将我们的返回值对吧 去进行比较 如果说你的这个函数对吧 它的返回值select函 返回值和老的值发生了变化不一样 引用不一样 那就会去更新页面 那use s select它是如何去更新页面的呢 啊实际上它的底层最核心的原理是用到了啊 react内部的一个方法叫做use reducer 它返回的第二个参数啊 实际上第二个参数 它是一个去渲染我们页面的一个方法 你直接去调用就好了 我们这个时候页面就更新了啊 啊这个就是又是select它的一个啊原理啊 好 Ok 我们接下来这里呢 我们来看一下react的一个渲染流程 那react的运行的主干逻辑啊 主要是包含以下三点 首先输入对吧 输入是什么呢 将每一次更新对吧 比如说新增删除修改节点之后诶 视为一次诶更新需求对吧 这个叫输入啊 比如说你set state啊 这个就是一次输入 而这个时候呢 因为react它新版本是基于任务调度的对吧 那所以第二个阶段呢 注册我们这个渲染的这个任务啊 它要在调度器里面去进行注册好 当我们的react reconcer收到更新需求之后 而是去调度中心的SCHEDU 去注册一个新的任务task 然后把这个更新需求转换成一个啊 哎转换成一个任务好 接下来第三个阶段就执行对吧 唉调度中心呢schedule 通过任务调度循环来执行我们的这个任务好 所以呢他们两个是相辅相成的 那实际上执行任务它主要分为两个阶段啊 一个是fire的发一把书的构造啊 第二个阶段commit啊 构造完之后 将我们的这个fib数啊 渲染到最终的页面上面去 那react的渲染流程呢 它又分为render和commit阶段 那render阶段呢 主要是将我们的微动转化成fiber数啊 那在commit阶段上去更新DOM啊 执行effect等副作用逻辑 那commit阶段它又分为三个阶段啊 before metation对吧 普通ATION和layout3个小阶段 那这里呢有一个需要注意的问题 就是render阶段啊 render阶段是可以打断的 这个实际上就是哎fiber架构它的一个核心 那render阶段它是可以打断的啊 是有优先级的 而且render有可能执行多次 那commit commit它的特点是什么 commit它的特点就是同步的啊 commit他的是同步的 所以这三个阶段他是依次执行的啊 那我们大名鼎鼎的啊 我们大名鼎鼎的几个护士士 比如说在比form tention里面呢 就会去执行use effect 他的回调 那在layout阶段呢就会去执行use net effect啊 那在mutation这个阶段呢就去更新我们真实的DOM 所以use layout effect 它的执行一定是在页面更新之后 那又是effect的执行呢 实际上也在页面更新之后 为什么呀 因为use effect是什么 是异步执行的 是什么 什么任务异异步执行呢 它是红任务异步执行啊 虽然说他的调用在我们的页面更新之前 但是它的执行啊确实在页面更新之后 因为他是宏任务异步执行的 OK这个就是react的一个啊渲染流程啊
