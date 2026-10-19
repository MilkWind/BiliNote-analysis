# 【2026最新】挑战7天刷完web前端面试高频题，让你稳稳拿下前端offer！ p69 vuex介绍以及深入使用

## 目录
- Vuex 核心概念与数据链路 *Content-[00:00]
- Vuex 的主要特点 *Content-[02:42]
- Vuex 实操：创建与配置 Store *Content-[04:10]
- Vuex 实操：在组件中使用与状态修改 *Content-[07:17]
- Vuex 辅助函数与扩展学习 *Content-[10:58]
- AI 总结 *Content-[11:25]

## Vuex 核心概念与数据链路 *Content-[00:00]

Vuex 是 Vue.js 的集中式状态管理工具，其核心在于维护一个单向的数据流。理解其数据链路是掌握 Vuex 的关键。

- **核心组成部分**：
  - **state**：作为集中式的状态管理，存储全局状态。
  - **component**：视图组件，负责渲染状态并响应用户操作。
  - **action**：动作集合，用于处理用户的交互事件和异步操作。
  - **mutation**：变更集合，是修改 state 的唯一手段。

- **完整的数据链路（单向数据流）**：
  1\. **状态初始化与渲染**：`state` 中管理全局状态，通过 `render` 过程在 `component` 中进行渲染，完成项目的视图呈现。
  2\. **用户交互触发**：用户在组件中进行操作，触发相关事件。
  3\. **分发 Action**：组件通过 `dispatch` 的方式触发一个 `action`。
  4\. **提交 Mutation**：`action` 接收到事件后，通过 `commit` 的方式触发一个 `mutation`（注意：修改状态的唯一手段是触发 mutation）。
  5\. **修改 State**：`mutation` 执行同步逻辑，更改当前的 `state`。
  6\. **视图更新**：`state` 修改后，会重新触发对应的 `render`，组件随之进行重新渲染。

## Vuex 的主要特点 *Content-[02:42]

Vuex 在设计上遵循严格的规范，以保证状态管理的可预测性和可维护性。其主要特点包括：

- **显式的状态存储**：Vuex 的状态存储是显式的，这使得状态的追踪和调试更加清晰。
- **严格的状态修改限制**：不能直接修改 `store` 中的状态。改变状态的唯一途径是显式地 `commit` 一个 `mutation`。这确保了每次状态变更都有明确的记录。
- **Action 处理异步**：`action` 主要用于处理异步操作（如 API 请求），它不直接修改状态，而是通过提交 `mutation` 来间接修改。
- **Getter 计算派生状态**：`getter` 用于从 `state` 中派生出一些状态，类似于 Vue 组件中的计算属性（computed），具有缓存机制。
- **插件机制**：Vuex 提供了相应的插件机制，方便开发者扩展功能（如日志记录、持久化存储等）。

## Vuex 实操：创建与配置 Store *Content-[04:10]

在实际项目中，使用 Vuex 需要先进行安装，然后创建并配置 Store 实例。

- **创建 Store 实例**：
  - 使用 `createStore` 方法来创建当前的 `store`。
  - 通过 `export default` 导出配置好的 `store` 实例。

- **Store 的核心配置项**：
  - **state**：定义初始化的状态。通常返回一个包含默认数据的对象（如 `default state` 中包含 `count: 0`）。
  - **mutation**：用于同步修改状态。例如定义 `increment` 方法，接收 `state` 参数，并执行 `state.count++` 来修改状态。
  - **action**：用于处理业务逻辑或异步操作。接收 `context` 对象，通过 `context.commit('increment')` 来提交对应的 `mutation`，从而触发状态修改。
  - **getter**：用于定义派生状态。例如定义 `double` 方法，接收 `state`，返回 `state.count * 2`，以便在组件中获取计算后的值。

- **注入 Vue 生态**：
  - 在项目的入口文件（如 `main.ts`）中引入创建好的 `store`。
  - 因为 Vuex 相当于 Vue 的一个插件，所以需要通过 Vue 的插件使用方式，即 `app.use(store)`，将 `store` 实例注入到整个 Vue 生态中。

## Vuex 实操：在组件中使用与状态修改 *Content-[07:17]

配置好 Store 后，即可在 Vue 组件中获取状态并触发状态修改。

- **获取 State**：
  - 在组件中，通过引入并使用 `useStore` 组合式函数，获取当前的 `store` 实例。
  - 通过 `store.state` 即可访问到全局状态（如 `count` 值）并进行渲染。

- **修改状态的两种方式**：
  在组件中触发事件以修改 `store` 中的 `count` 值，主要有以下两种方式：
  1\. **通过 Action 修改**：调用 `store.dispatch('increment')`。这会触发 `action`，再由 `action` 内部 `commit` `mutation` 来修改状态。
  2\. **直接通过 Mutation 修改**：调用 `store.commit('increment')`。这会直接触发 `mutation` 来修改状态。

- **效果验证**：
  - 在组件中绑定点击事件，分别使用上述两种方式触发增加操作。
  - 测试结果表明，这两种方式都能成功且正确地统一去管理并修改 `store` 中维护的状态值。

## Vuex 辅助函数与扩展学习 *Content-[10:58]

除了基础的 API 调用，Vuex 还提供了一系列辅助函数，以简化组件中的状态映射，提升开发效率。

- **常用辅助函数**：
  - `mapState`：将 `store` 中的 `state` 映射到组件的计算属性中。
  - `mapGetters`：将 `store` 中的 `getter` 映射到组件的计算属性中。
  - `mapActions`：将 `store` 中的 `action` 映射到组件的 `methods` 中。
  - `mapMutations`：将 `store` 中的 `mutation` 映射到组件的 `methods` 中。

- **学习建议**：
  - 辅助函数能够大幅减少组件中重复的 `store.state.xxx` 或 `store.commit` 等样板代码。
  - 建议开发者前往 Vuex 官方网站查阅相关文档，官网上对这些辅助函数的使用场景和详细语法有非常细致的讲解。

## AI 总结 *Content-[11:25]

本视频详细讲解了 Vue 前端面试高频考点 Vuex 的核心概念与实战应用。
1\. **核心思想**：Vuex 采用集中式状态管理和严格的单向数据流（State -> View -> Actions -> Mutations -> State），确保了状态变更的可预测性。
2\. **核心 API**：明确了 `state`（存储状态）、`getters`（派生状态）、`mutations`（同步修改状态）和 `actions`（异步操作及提交 mutations）的职责划分。特别强调了**修改状态的唯一途径是 commit mutation**。
3\. **实战流程**：演示了在 Vue 3 中通过 `createStore` 创建实例，在 `main.ts` 中通过 `app.use()` 注入，以及在组件中通过 `useStore()` 获取状态和触发 `dispatch`/`commit` 的完整闭环。
4\. **进阶技巧**：提及了 `mapState`、`mapGetters` 等辅助函数，帮助开发者在大型项目中优化代码结构，提升开发效率。掌握这些内容对于应对前端状态管理相关的面试场景题至关重要。

---

## 文稿转写

那么接下来我们来看看相关的VX VX的一个介绍 VX介绍呢 相信这块儿同学们应该都比较熟悉呀 那么VX它主要包含这么几部分 首先就是我们当前的state 当前state the state呢 就是我们去作为我们状态管理的这种集中式的 去进行状态管理 那么我们the status会通过最终渲 在我们的component去进行一个渲染 完成我们的先项目渲染 那么我们用户会在我们当前 组件当中去进行修改 当现当前的状态 一般我们就通过dispatch一个action的方式 所以说我们会有这样一个action的一个集合 那么我们通过用户dispatch一个action 那么我们这个action我们修改状态的唯一手段 我们需要触发一个mutation 所以这是比拼点 而它的一个繁琐的地方 它会有这么几个区分对吧 我们mutation去更改我们当前的state 去更改我们当前的state 我们在这里去commit一个musician嗯 所以说我们 这是在VX对整体的一个数据链路 修电路 我们通过在state当中去管理我们当前全局的状态 然后我们再通过render 继续去在我们component当中去进行渲染 那么我们用户操作去触发事件 通过dispatch exaction方式去触发相关的事件 那么我们在想要去更改最终state呢 我们通过需要去commit一个musician Musician 再去muted的我们当前一个状态 那么状态就发生了修改 修改了以后呢 我们会重新触发对应的render 那么我们的组件也会进行触发重新的一个渲染 所以说这是我们这样的一个VUE X的一个数据链路 这里就包从其中的action mutation和state 就是在我们VS当中 它vs 所以VS包含这么几盘内容 它是包含这么几块内容的 好我们使用VX呢需要先去进行一个安装 比如说我们之前已经安装过 我们先去vie安装项目当前VX 那么安装完以后呢 我们就需要去使用当前的这样一个状态 那么vs呢它主要有这么几个特点 首先VX的状态存储状态是我们从状态显示的 另外呢我们它是不能去直接修改状态 不能直接修改 不能直接改变我们store中的状态 改变我们store中的状态 唯一的途径啊 就是通过显示的去commit it 我们的一个musician commit了一个mutation之后 它去来我们当前的一个修改状态 我们action呢主要用于我们的异步操作 以get呢去用来我们一些呃计算派生的一些状态 就类似我们这样一个计算属性 以及我们还有对应那些相关的插件机制 都是我们VX相关的一些内容 那么我们简单给同学们去做一个呃实操啊 那么因为同学们对这块应该是非常的熟悉啊 所以VX就不是我们当前那个重点的内容 那么我们看看它是大概如何去使用 我们需要创建我们当前store 在store当中呢去做我们状态的一个维护 我们一般通过以下几个数的 通过create store来去创建当前1store 我们一般通过export default 我们当前store 那么store当中呢包含以下几个内容 首先就是我们当前state state呢 我我们可以定义一个初始化的state 那么我们在state当中 我们就return default state 好那么我们就包含几part内容 一个是mutation对吧 我们刚刚有介绍 我们首先mutation里面就是用来去哦 同步的去修改我们当前的状态 比如说我们需要去修修改当前state 我们在我们增加单in state 我们就通过increment我们state 然后state count加加 那么以及我们还有对应的action action呢我们同理也是需要提供对应的额增加的 他的方法 那么我们action需要接受对应commit 我们通过commit一个MUSICI 比如说commit我们increment对吧 我们MIDITION里面的CREMENT 这样的话就会去触发 把我们当前state给到它 我们去修改当前的状态好 另外这是我们action 我们同理我们GADGE去一些派生的相关的方法 比如说我们double 我们获取一个哦当前count的一个double double变量 所以通过这COLLASH里面的double 去获取这样一个double state好 那么接着呢就需要在我们点TS当中去作为 把我们当前state作为一个引入 那么之后呢我们就通过插件的方式 通过use的方式去住 因为我们呃VX其实也相当于vi view的一个插 一个插件 所以啊view的使用插件的方式 就通过点击use的方式来去呃 嗯我们的入参就是对应的插件的相关实例 好 这样的话我们就注入到当整个view的生态当中 好就我们这样就可以去使用 那么我们可以建一个当前VX的组件 我们可以通过use store方式去使用 当前的state 好我们来看一下对应的效果 那么我们接下来呃 这是渲染 我们也可以去修改 基于我们通过store点dispatch increment 去增加相关内容 我们也可以通过呃 通过store commit后面一个increment 就这两种方方法都是都是OK的 通过commit commit的方式 通过dispatch的方式好 我们来看一下 好我们看一下效果 我们通过点击 这两个都是没问题对吧 我们一个通过action的方式 一个通过commit的方式来去全统一去管理 当前我们通过VX的方式去维护 我们当前这个store里面有一个count值 然后在我们VX当中 这就是我们通过VX的一个使用方式啊 当然我们可能还有啊 VX还有其他的一些手段 一些使用方式 比如说我们一些辅助函数 像map state呀 map geatters啊 我们my actions 还有我们的MAMOVISIONS啊等等 这都是我们相关的一些辅助函数 那么也都是有助于去提升 我们使用我们VX的整体的一个 效率的一个方式 那么这里就不是我们今天重点啊 所以到时这块同学们可以去看一下 他们的相关官网 官网上也都讲的非常详细细致
