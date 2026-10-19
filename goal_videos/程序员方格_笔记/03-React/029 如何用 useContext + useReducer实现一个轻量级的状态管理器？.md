# 10月丨建议你的【React】达到这种程度，再去面试前端开发！ p30 第27集：如何用 useContext + useReducer实现一个轻量级的状态管理器？

## 目录
- 引言与背景
- 核心概念解析：useContext 与 useReducer
- useContext 与 useReducer 结合使用的优势
- 实现轻量级状态管理的五个步骤
- 代码示例：实现全局计数器
- 面试表达指南与方案描述
- 面试常见场景题解析
- 总结与回顾
- AI 总结

## 引言与背景 *Content-[00:01]
- 在开发 React 应用时，状态管理是一个绕不开的核心话题。
- 当组件层级比较深时，传统的 props 逐层传递（即 **Prop Drilling**）会变得非常繁琐且难以维护。
- 为了更加优雅、轻量地处理全局或跨组件的状态，我们可以使用 React 自带的 `useContext` 和 `useReducer` 这对组合，来实现一个轻量级的状态管理库。

## 核心概念解析：useContext 与 useReducer *Content-[01:27]

### useContext
- **作用**：React 提供的一种机制，允许在组件树中进行跨层级的直接数据传递，无需手动逐层传递 props。
- **核心 API**：
  - `React.createContext`：用于创建上下文（Context）对象。
  - `Context.Provider`：Provider 组件是 Context 对象里的一个属性。被它包裹的任何子组件，都可以通过 `useContext` 或 `Context.Consumer` 来消费数据。
- **通俗理解**：就像一个公共频道，Provider 负责发布信息，订阅了该频道的组件都能接收到数据。

### useReducer
- **作用**：可以看作是 `useState` 的增强版，特别适合管理逻辑比较复杂的状态（例如状态包含多个部分，或下一个状态的值需要依赖上一个状态进行计算）。
- **机制**：接收一个 `reducer` 函数来集中处理所有的状态更新逻辑，使代码更加清晰、有组织。
- **工作方式**：调用 `dispatch` 函数并传入一个 `action`，`reducer` 会根据这个 `action` 计算并返回新的状态。这种模式与 Redux 的核心思想非常相似。

## useContext 与 useReducer 结合使用的优势 *Content-[03:31]
将这两个 API 结合使用，能够实现强强联合：
- **逻辑集中**：`useReducer` 帮我们将状态逻辑（如何更新状态的方法）集中管理起来，使得状态变更变得更加清晰且可预测。
- **数据注入**：`useContext` 负责将 `useReducer` 返回的 `state` 和 `dispatch` 函数注入到组件树中，让任何需要的子组件都能方便地访问和使用，从而彻底避免繁琐的 props 传递。
- **方案优点**：
  - React 原生支持，非常轻量，不需要引入额外的第三方库。
  - 代码结构清晰，实现了状态管理与 UI 展示的分离。
  - 对于中小型项目，或者大型项目中的某些独立模块来说，是一个非常棒的选择。

## 实现轻量级状态管理的五个步骤 *Content-[04:40]
具体实现步骤非常清晰简单：

1\. **创建 Context 对象**：使用 `React.createContext` 创建一个 Context 对象，该对象将用来共享状态和派发函数。
2\. **定义 Reducer 和初始状态**：定义 `useReducer` 所需的 reducer 函数和状态的 `initialState`。Reducer 负责根据接收到的 `action` 来更新状态。
3\. **创建 Provider 组件**：这是关键一步。在组件内部调用 `useReducer` 获取当前的 `state` 和 `dispatch` 函数，然后通过第一步创建的 `Context.Provider`，将 `state` 和 `dispatch` 作为 `value` 传递给所有子组件。
4\. **创建自定义 Hook（强烈推荐）**：创建一个如 `useMyStore` 的自定义 Hook，内部直接调用 `useContext` 来获取 Context 中的 `state` 和 `dispatch`。这样在业务组件中调用该 Hook 会更加语义化，代码也更简洁。
5\. **在业务组件中使用**：在业务组件中通过自定义 Hook（或直接用 `useContext`）拿到 `state` 进行展示，并拿到 `dispatch` 函数来派发 `action` 和更新状态。

## 代码示例：实现全局计数器 *Content-[06:37]
目标：创建一个全局计数器，可以在不同的组件中增加或减少它的值，并且都能看到最新的计数。

### 1. 定义状态管理的核心部分（store.js / context.js）
通常我们会单独起一个文件来定义核心逻辑：
- **Initial State**：非常简单，只有一个 `count` 属性，初始值为 0。
- **Reducer 函数**：接收当前的 `state` 和一个 `action` 对象，根据 `action.type` 判断是执行 `increment`（加一）、`decrement`（减一）还是 `reset`（重置为零）。注意这里必须返回一个新的状态对象。
- **创建 Context**：使用 `React.createContext` 创建 `CounterContext`。
- **CounterProvider 组件**：内部调用 `useReducer`，传入定义好的 reducer 函数和 initialState，得到当前的 `state` 和 `dispatch` 函数。然后通过 `CounterContext.Provider` 将 `{ state, dispatch }` 作为 `value` 传递下去。
- **自定义 Hook (`useCounter`)**：封装了 `useContext(CounterContext)` 的调用，并做了一个保护机制（如果没有在 Provider 内部调用会抛出错误），让业务组件用起来更方便。

### 2. 在应用中调用（App.js）
- 在 `App.js` 的顶层，使用 `CounterProvider` 将需要共享状态的组件（如 `DisplayCounter` 和 `Controls`）包裹起来。
- **DisplayCounter 组件**：调用 `useCounter` 拿到 `state`，展示 `state.count`。
- **Controls 组件**：调用 `useCounter` 拿到 `dispatch` 函数，在按钮的点击事件里，通过 `dispatch` 发送不同 `type` 的 `action` 来更新状态。

## 面试表达指南与方案描述 *Content-[10:04]
在面试中，当被问及如何设计状态管理时，可以按以下逻辑描述该方案：

- **场景引入**：当应用需要一些全局状态（如用户登录信息、主题配置），但引入像 Redux 这样的库对当前项目规模来说有点重时，我们会考虑使用 React 内置的 `useContext` 结合 `useReducer` 实现轻量化状态管理。
- **核心思路**：用 `useReducer` 定义和管理状态的初始值以及所有可能的状态变更逻辑（集中管理）；然后通过 `useContext` 创建一个 Provider，将返回的 `state` 和 `dispatch` 函数注入到组件树中。任何需要这些状态或操作的子组件，都可以通过 `useContext` 或封装好的自定义 Hook 来获取，从而避免 props 的层层传递。
- **强调优点**：代码简洁，React 原生支持，不需要额外的学习成本，理解和上手都非常友好。
- **提及局限性**：
  - Context 的 value 发生任何变化时，默认会导致所有消费该 Context 的组件重新渲染。虽然可以通过 `React.memo` 或将 Context 拆分成更细粒度的组件来优化，但在非常复杂的应用中，性能调优需要更多关注。
  - 相比 Redux，它缺少一些成熟的生态支持，比如强大的开发者工具或复杂的中间件机制。

## 面试常见场景题解析 *Content-[12:38]
这个知识点在面试中还会以以下场景题的形式出现：

- **状态管理方式对比**：谈谈在 React 中进行状态管理的几种方式及优缺点。此时 `useContext` + `useReducer` 就是一个除了 `useState`、Redux、Zustand 之外的重要方案，可以重点分析它在轻量级场景下的优势。
- **全局主题切换功能**：如果让你实现一个网站的暗黑模式和明亮模式切换，你会怎么设计？这非常适合用该组合解答。将当前主题（`dark` 或 `light`）作为 `state`，切换主题的动作作为 `action`，用 `useReducer` 实现逻辑，用 `useContext` 共享状态。
- **实现购物车功能**：在不使用任何第三方状态管理库的情况下，如何实现购物车功能？购物车的核心逻辑包括商品列表的添加、删除、修改数量等，这些操作都可以用 `useReducer` 进行状态管理，然后用 `useContext` 把购物车状态和操作函数共享给相关组件。

结合具体场景给出方案，能让面试官认可你对 React Hook 的理解和实际应用能力。

## 总结与回顾 *Content-[14:32]
- `useContext` 是解决数据跨组件传递（Prop Drilling）问题的 Hook。
- `useReducer` 是 `useState` 的升级版，更适合管理复杂的状态逻辑，让状态变更的意图变得更加明确。
- 这两者结合构成了一个非常实用的、React 原生的轻量级状态管理模式。
- 核心是通过一个 Provider 组件来封装由 `useReducer` 管理的 `state` 和 `dispatch` 函数，子组件通过 `useContext` 方便地消费这些方法和状态。
- 该方案非常适合中小型应用，或者大型应用中独立模块的状态管理，能让代码更加清晰、易于维护。

## AI 总结
本视频详细讲解了如何利用 React 原生的 `useContext` 和 `useReducer` 构建轻量级状态管理器。通过 `useReducer` 集中处理复杂的状态更新逻辑，并结合 `useContext` 跨越组件层级共享状态与派发函数，有效解决了 Prop Drilling 问题。该方案无需引入第三方库，代码结构清晰，非常适合中小型项目或大型项目的独立模块。视频不仅提供了全局计数器的完整代码实现，还针对前端面试提供了场景化的表达指南与常见考题解析，帮助开发者在面试中展现扎实的 React 状态管理能力。

---

## 文稿转写

如何用use context和use reducer 实现一个轻量状态管理库 Hello 大家好 我是方格 今天我们来聊一个在面试中经常会被问到的 也是非常实用的react的知识点 嗯如何使用react自带的use contact和use reducer 这对组合来实现一个轻量的状态管理库 在开发react react应用时 状态管理是一个绕不开的话题 当组件层级比较深的时候 呃 传递props的啊 传统的一个props组成传递 也就使我们常说的prop trailing 会变得非常的繁琐和难以维护 那么有没有没有一种更加优雅 更加清亮的方式来处理啊 全局或者跨组件的状态呢 当然有 那就是今天的主角啊 use context加上use reducer 我们是我们会首先分别理解这两个hook的作用 然后看看他们如何协同工作 最后通过一个代码示例来加深理解嗯 还会聊一下在面试时如何表达这个方案 首先我们看一下这个use context 简单来说use context是react提供的一种机制 它允许我们在组件书中嗯 做跨层级的直接数据传递 而不用手动的一层一层去传props嗯 然后它的核心API嗯就包括了react se context recipe点 Create context 这是可以用来创建上下文对象的方法 然后还包括呃context and provider啊 这个组件它是呃通过create context 去创建了一个对象里里面的一个属性啊 他这个组件呢就可以啊 任何这个在这个provider组件下的一个子组件 都可以通过use context 或者是用这个contest and consumer来消费这个数据 这就好比有个公共频道 然后provider去发布信息 然后订阅了这个频道的组件都能收到 好的 接下来是use啊 Use reducer 你可以把它看作是you state的一个更加强大的版本 它特别适合管管理那些逻辑比较复杂的状态嗯 当你的状态有好几个部分或者下一个状态的值 需要依赖上一个状态去计算时 你就用use reducer 它就可以让这个代码更加清晰 更加有组织嗯 他接收一个reducer函数来集中处理所有的状态 更新逻辑嗯 你你然后你调用这个dispatch函数 传入一个action啊 reducer就会根据这个action来计算 并且返回新的状态 这个模式其实就和REDUX的核心思想 是非常相似的 额那我们为什么把这个use reducer和use context 去结合起来用呢 啊这就是他们的所谓的这两个API的强强联合啊 首先use reducer就帮我们把这个状态逻辑 比如啊 如何更新状态的一个方法去集中地管理起来 使得这个状态变得更加清晰而更加可预测 而use context呢则负责把USREDUCER返回的 state和dispatch函数注入到一个组件树中 让任何需要的一个子组件 都能方便的去访问和使用它们 从而避免了繁琐的呃props传递 那么这样做的好处就是显而易见的 它是啊react原生的非常清亮 不需要引入额外的库 然后代码结构也很清晰 状态管理和UI展示分离啊 对于中小型项目或者大型的项目中的某 些独立模块来说 这是一个非常棒的选择 好在理解他的优势之后呢 那么具体该怎么实现呢 其实步骤就非常清晰简单 首先第一步我们用一个U啊 react点concreate contact去创建一个context对象 然后这个context啊 将用来共享我们的状态和派发函数 然后第二步我们需要定义我们的USA reducer函数和状态的initial state 然后reducer负责根据啊接收到的action来更新状态 然后第三步是创建一个啊provider组件 这个组件是关键 它会内部会调用use reducer 来获取当前的state和props啊和dispatch函数 然后通过我们的第一步创建的context provider 把state和dispatch作为value传递给啊 所有他的子组件 然后第四步也是呃可选 但比较强烈推荐的就是创建一个自定义的hook 比如说叫做use my store 在这个hook中直接调用use context 来获取context中的state和呃dispatch 这样的话在业务组件里面就可以调用这个hook 来获取这个数据嗯 这样就更加语义化 同时代码会更加简洁 然后最后一步就是在我们的业务组件中 通过这个自定义hook 或者是直接用这个use context拿到这个state进行展示 以及拿到这个dispatch函数 没有没有没有来派发action和更新状态 好理论说完了 我们接下来通过一个实际的一个代码示例 来看一下 这样就更加直观一点好 现在我们的目标就是创建一个全局的计数器 我们可以在不同的组件中去 增加或者减少它的值 并且都能看到最新的技术嗯 首先来到一个进定义状态管理的核心部分 通常我们会单独起个文件 就是这里的store点JS或者context点JS 然后 额首先是这个initial state它非常简单 只有一个count属性 初始为零 然后是reducer函数 它接收当前的state和一个action对象 然后根据action点type判断我们是执行啊 an increment加一还是decrement减一 还是reset重置为零 注意这里我们会返回一个新的状态对象啊 然后紧接着我们要啊 我们用这个create context去创建了我们的counter context呃 核心就是这个counter provider组件 它内部啊用了这个use reducer 然后传入了我们的我们定义的一个reducer呃 传入我们定义的一个reducer函数 和一个initial state 得到是当前的state和dispatch函数 然后通过啊counter context and provider 把包裹的一个state和dispatch的对象 作为value去传递下去 所有被这个context content provider给包裹的子组件都能够访问到这个value 最后我们还啊还会自定义了一个hook 叫做ruth counter 它封装的是啊use context里面content context的调用 并且做了个保护 如果没有在provider内部调用 会抛出一个错误 这样让我们的业务组件用起来会更加方便一些 好现在看看我们在啊应用中该如何调用它啊 假设我们有个i app等JS 然后大家看到在啊app点JS的顶层啊 app的顶层啊 我们把这个counter provider用control provider 把这个要共享状态的一些组件 比如说我们这里有两个 一个是display counter 一个是controls去包裹起来 然后在display counter里面呢 我们呃调用use counter去拿到这个state 然后展示state点count 然后在controls里面呢 我们啊同样的去调用这个啊 use counter里面的dispatch函数 然后在按钮的点击事件里 通过dispatch发送不同的type的action 来更新一个状态 所以啊通过刚才的一些代码示例啊 相信大家对啊 Use context 加入reducer 这个啊简易的状态管理器有了具体的了解啊 这个是比较基础也比较核心的代码逻辑啊 如果你在面试中能够清晰的表达 并且写出来会非常加分的 好了 前面我们看完了代码 那么在面试中 当面试官问你相相关的问题时 我们应该如何描述这个方案呢 首先你可以从遇到的场景入手 比如当我的应用需要一些全局状态 比如用户登录信息呀 主题配置啊 但是我又觉得呃引入像REDUX这样的库 对于当前的项目规模来说有点重的时候 我们就会考虑呃react内置的use context 结合use reducer这样的方案 实现一个轻量化的将呃状态管理 然后你要点出一个核心思路 就是我会用use reducer来定义和管理 状态的初始值 以及所有可能的状态变更逻辑 这部分是集中的 然后通过use contest创建一个provider 将USREUSER返回的state和dispatch函数 注入到组件数中 这样任何需要这些状态或者操作的子组件 都可以很方便地通过use context啊 或者一个封装好的自定义hook来获取 这样就避免了主啊props的层层传递 然后可以强调一下 这种方案的优点 代码比较简洁 是react原生支持的 不需要任何的额外的学习成本 所以对于理解和上手都比较友好 当然也要提提到他的一些局限性 比如说呃context的value发生任何变化 默认会导致所有消费这个context的组件 都要重新渲染 虽然可以通过呃react a点memo 或者将context拆分成更细粒度的啊 一些组件来优化 但是在非常复杂的应用来说 性能调优啊 可能需要更多的关注相 另外呢相比REDUX 它可能还更缺少一些成熟的生态支持 比如说强大的开发者工具啊 或者是复杂的中间件机制 那么我们再看一下啊 这个知识点 在面试里还会以什么形形式去出现啊 首先比如面试官可能会问 你 就是在谈谈在react中进行状态管理的几种方式 以及优缺点啊 这时候呢use context加use reducer 就是一个除了use state UREDUXJUSTIN这些之外的一个重要方案 你可以分析他在轻量级场景下的一些优势 或者更具体一点 如果让你实现一个呃全局的装主题切换功能 比如网站的暗黑模式和明亮模式的切换 你会怎么设计 这就是一个非常适合 网站的暗黑和明亮主题切换 就是一个非常适合用呃 use context和use reducer来解答的场景 你可以把当前的主题 比如说duck或者like就作为一个state 然后切换主题的动作作为action 你去用UREDUCER去来实现 然后再比如在不使用任何第三方 状态管理库的情况下 如何实现一个购物车功能嗯 一购物车的核心逻辑 就包括了一些商品列表的啊添加 然后删除嘛 然后还有修改数量 这些操作 你都可以用use reducer来进行状态的管理 然后用use context 把啊购物车状态和操作函数 共享给相关的一些组件嗯 所以当你能结合具体场景来给出一些方案时 面试官会认可你对这个react hook的理解 和实际的应用能力 好我们来快速回顾一下今天的主要内容 我们首先了解了啊 Use context 他是作为呃一个解决数据跨组件传递的一个啊 props string问题的一个hook 然后use reducer是啊use state的升级版 更适合管理复杂的状态逻辑 让这个状态变更的意图变得更加明确 这个模式呢就构成了一个非常实用的 轻量级的react原生的状态管理模式 它的核心就是通过一个provider组件来封装 由use reducer管理的state和dispatch函数 然后子组件通过use context来方便去消费这些方 方法和状态啊 这个方案就非常适合中小型的应用 或者大型应用中的一些独立的模块的状态管理 它就能让你的代码更加清晰 也更加容易维护 好今天以上就是今天的内容 希望今天关于use contest和use reducer 这个组合的内容对你有所帮助啊 我是方格 我们下期再见
