## 目录
- 为什么要测试自定义 Hook
- 测试 Hook 的核心挑战与解决思路
- 核心工具与 API 介绍
- 实战场景一：测试初始状态
- 实战场景二：测试状态更新与 act 函数
- 实战场景三：测试 Props 变更与 rerender 函数
- 实战场景四：测试异步操作与 waitFor 函数
- 面试实战：如何回答 Hook 测试相关问题
- 核心知识点总结
- AI 总结

## 1. 为什么要测试自定义 Hook *Content-[01:10]
- **逻辑复杂性**：Hook 往往封装了应用中最复杂的逻辑，如数据请求、状态管理、复杂计算等，是应用稳定性的基石。
- **复用风险**：Hook 的核心价值在于复用。一个存在 bug 的 Hook 会把问题扩散到所有使用它的组件中，后果不堪设想。
- **天然解耦**：自定义 Hook 天然地将逻辑和 UI 分离，这使得它成为单元测试的完美对象。
- **测试目的**：保证 Hook 的行为在任何情况下都与预期完全一致。

## 2. 测试 Hook 的核心挑战与解决思路 *Content-[02:02]
- **核心挑战**：React 的核心规则规定，Hooks 只能在 React 组件或另一个自定义 Hook 的函数体中调用。
- **错误示例**：不能像测试普通 JavaScript 函数那样直接 `import` 并调用自定义 Hook（例如直接调用 `useCounter`）。这会立即抛出著名的 `Invalid hook call` 错误，因为它脱离了 React 组件的上下文环境。
- **解决思路**：既然 Hook 需要宿主环境，我们就为其虚拟创建一个测试组件。让该组件调用 Hook，然后通过测试组件的行为（如渲染内容、状态变化）来间接判断 Hook 是否工作正常。
- **工具引入**：手动创建宿主环境非常繁琐，RTL（React Testing Library）家族提供了 `@testing-library/react-hooks` 库。它包揽了创建宿主环境的所有工作，并提供了一套简洁优雅的 API，让我们能专注于测试 Hook 本身的逻辑。

## 3. 核心工具与 API 介绍 *Content-[04:05]
- **核心 API**：`renderHook`。
- **基本用法**：从 `@testing-library/react-hooks` 导入 `renderHook` 方法。传入一个回调函数，在回调函数内部真正调用自定义 Hook。
- **返回值解析**：`renderHook` 返回一个包含 `result` 的对象。`result.current` 指向自定义 Hook 当前的返回值，无论是状态值（如 `count`）还是方法（如 `increment`），都可以从这里获取。

## 4. 实战场景一：测试初始状态 *Content-[05:05]
- **测试目标**：验证 Hook 能否正确接收并使用传入的初始值。
- **示例 Hook (`useCounter`)**：接受 `initialValue`，内部用 `useState` 维护 `count` 状态，返回 `count` 及操作函数（`increment`, `decrement`, `reset`）。操作函数均使用 `useCallback` 包裹，以确保引用稳定性，避免不必要的重渲染。
- **测试逻辑**：
  - 调用 `renderHook`，在回调函数中传入数字 `10` 作为初始值调用 `useCounter(10)`。
  - 进行断言：期望 `result.current.count` 的值为 `10`。

## 5. 实战场景二：测试状态更新与 act 函数 *Content-[06:54]
- **关键痛点**：在 React 中，`useState` 或 `useReducer` 触发的状态更新是异步执行的。不能在调用更新函数后立即断言新状态，否则会导致测试失败。
- **解决方案**：使用 Testing Library 提供的核心工具 `act` 函数。
- **核心原则**：任何会导致 Hook 状态更新的操作，都必须包裹在 `act` 的回调函数里。`act` 会确保其内部触发的所有更新处理完毕后，再去断言拿到的最新状态。
- **测试逻辑**：
  - 使用初始值 `0` 渲染 Hook。
  - 将 `result.current.increment()` 调用放入 `act` 中，执行完毕后断言 `count` 变为 `1`。
  - 将 `result.current.decrement()` 调用放入 `act` 中，执行完毕后断言 `count` 变回 `0`。

## 6. 实战场景三：测试 Props 变更与 rerender 函数 *Content-[09:02]
- **测试场景**：真实世界中，组件会因父组件的 props 变化而重新渲染。如果 Hook 依赖了这些 props，需要测试其响应行为。
- **解决方案**：使用 `rerender` 函数模拟组件重渲染。
- **配置方法**：
  - 在调用 `renderHook` 时，除了 `result`，还可以解构出 `rerender` 函数。
  - 传递给 `renderHook` 的回调函数需要能接收 `props` 参数。
  - 在 `renderHook` 的第二个参数（配置对象）中，通过 `initialProps` 提供初始属性。
- **测试逻辑（验证 `reset` 函数行为）**：
  - 使用初始值 `0` 渲染 Hook，调用 `increment` 使 `count` 变为 `1`。
  - 调用 `rerender`，传入新的 `props`（将 `initialValue` 改为 `10`），模拟组件重渲染。
  - 在 `act` 中调用 `reset` 函数。此时 Hook 内部依赖的 `initialValue` 已更新为 `10`。
  - 断言 `count` 等于 `10`，证明 Hook 在 props 更新时行为正确。

## 7. 实战场景四：测试异步操作与 waitFor 函数 *Content-[12:06]
- **测试场景**：Hook 内部包含异步操作（如 fetch 数据请求）。
- **解决方案**：使用 Testing Library 提供的异步工具函数 `waitFor`。
- **测试逻辑（以假设的 `useFetch` 为例）**：
  - 将测试函数设为异步（`async`）。
  - 使用 `jest.mock` 或类似工具模拟一个 fetch 请求。
  - 使用 `renderHook` 渲染 Hook，初始断言 `loading` 状态应为 `true`。
  - 使用 `await waitFor`：它会反复执行传入的断言，直到通过或超时。在此等待 `loading` 状态变成 `false`。
  - `waitFor` 执行完毕后，说明异步请求已完成，此时可安全地对最终的 `data` 结果进行断言。

## 8. 面试实战：如何回答 Hook 测试相关问题 *Content-[14:00]
- **面试题**：在项目中，你如何保证自定义 Hook 的质量和稳定性？如何对封装了异步请求（如 `useFetch`）的 Hook 进行测试？
- **回答策略（分步骤展示逻辑层次）**：
  1. **点明中心思想**：强调自定义 Hook 是逻辑复用的核心，稳定性至关重要，编写单元测试是项目质量保障体系必不可少的一环。
  2. **点名使用工具**：说明团队统一使用 RTL 提供的 `@testing-library/react-hooks`。解释其优点：能够自动创建隔离的测试环境来渲染 Hook，让开发者专注于测试逻辑本身。
  3. **分场景描述测试策略（核心得分点）**：
     - **初始状态**：用 `renderHook` 渲染，直接断言 `result.current`。
     - **状态更新**：将触发更新的操作包裹在 `act` 中，确保断言时状态已同步。
     - **依赖外部 Props 更新**：使用 `rerender` 函数模拟组件重渲染，测试 Hook 的响应。
     - **异步逻辑**：结合 `act` 和 `waitFor` 工具函数，等待异步操作执行完毕后再对最终状态和结果断言。同时使用 `jest.mock` 或 `spyOn` 模拟真实 API 请求，确保测试的独立性和高效性。

## 9. 核心知识点总结 *Content-[16:43]
- **标准测试库**：`@testing-library/react-hooks`。
- **核心 API 速记**：
  - `renderHook`：用于渲染 Hook。
  - `result.current`：用于访问 Hook 的当前返回值/结果。
  - `act`：用于包裹状态的更新操作。
  - `rerender`：用于模拟组件重渲染（更新 Props）。
  - `waitFor`：用于处理异步操作。
- **核心测试思想**：像用户一样关注 Hook 的输入和输出，而不是其内部实现细节，这正是 Testing Library 所倡导的理念。

## AI 总结
本视频详细讲解了在 React 面试中如何回答“如何测试自定义 Hook”这一高频问题。视频首先明确了测试自定义 Hook 的重要性及脱离 React 上下文导致的 `Invalid hook call` 挑战，随后引入了 `@testing-library/react-hooks` 作为标准解决方案。通过四个递进的实战场景（初始状态、状态更新、Props 变更、异步操作），详细演示了 `renderHook`、`act`、`rerender` 和 `waitFor` 等核心 API 的具体用法。最后，视频提供了一套结构化的面试回答话术，帮助求职者从工具选择到分场景策略，全面展现对 Hook 单元测试的掌握深度，强调了关注输入输出而非内部实现的 Testing Library 核心理念。

---

## 文稿转写

如何测试一个自定义hook Hello 大家好 欢迎来到本期的react面试系列 我是方格 在react开发中呢 我们经常会把可复用的逻辑 封装成自定义的hook 但是问题来了 这些不带UI的纯逻辑单元 我们应该如何保证它的质量呢 今天我们就来深入探讨一个非常重要的话题 就是如何测试一个自定义hook 那么在这一集里呢 我们先会搞清楚为什么要给自定义写 自定义hook写单元测试 然后我们会一起揭开测试hooks时 遇到的一个核心挑战 当然最关键的是我们会手把手的带你掌握啊 RTL的react hooks这个强大的工具 让你能够像测试普通主线一样 轻松的为你的hook编写出健壮的 可靠的测试用例 我们先来建立一个共识 为什么要费心去测试hook 首先hook啊 往往封装了我们啊最应用中最复杂的逻辑 比如数据请求 状态管理啊 复杂的计算等等 这些是应用稳定性的即时 其次呢 hook的核心价值在于复用 一个有bug的hook 会把问题带到所有使用它的组件里面 后果不堪设想 最重要的一点 自定义户口天然地将逻辑和UI分离 这使得它成为了单元测试的完美对象 所以测试的最终目的就是保证hook的行为 在任何情况下都和我们预期的一致 好那既然要测 那挑战在哪呢 那最大的挑战就来自于react的核心规则 hooks只能在reactor组件 或者另外一个who自定义的hook函数体中调用 这就意味着 我们没有办法像测试一个普通的JAVASCRIPT函数那样 去简单的把它import进来 然后直接调用它 我们来看一个错误示例 比如你看我 我们现在像这样 在直接的在测试文件中去调用 这个我们自定义的use count react Vue react 就会立即抛出一个啊著名的错误 Invalid hook call 因为它脱离了组件react组件的上下文环境额 那么正确的思路是什么呢 既然他需要一个加一个宿主环境 我们就给他制造一个加 具体来说就是在测试的时候正哦 我们会虚拟的创建一个啊测试组件 让这个组件去调用我们的hook 然后我们会通过测试这个组件的行为 比如它渲染了什么 他的状态如何变化 去间接的判断我们的hook工作是否正确 啊啊首先手动这创建这个速度环境非常繁琐 好在呢啊 Testing like RTL的家族 已经为我们提供了一个完美的解决方案 它就是啊red at hooks gu 这库 这个库会把所有创建数组环境 的脏活累活都包揽 并且提供一套非常简洁优雅的API 让我们能专注于测试hook本身的逻辑 首先这个库最核心的API啊 就是render hook 它的用法非常直观 我们就直接从首先我们直接从这个呃杠 react hooks这里面去导入我们的render hook方法 然后去调用它啊 注意我们传给他的是个回调函数 在这个回调函数里 我们才去真正的调用自己定义的一个use counter 这个hook render hook会返回一个包含一个result的对象 这个result有一个很重要的属性叫做current I result 点current它就指向了我们use conuse counter hook 当前的返回值啊 无论是状态值 account还是increment 这些方法都可以从这里拿到 好我们再来看看一个实际的例 一个实战例子 我们会以我们的一个use counter这个户口为例 去编写一段代码 首先先快速过一下我们的自定义hook的源码 它非常简单 接受一个initial value 然后内部的use count 用state去维护一个count的状态 然后它返回一个状态 返回一个呃 返回一个状态对象 然后里面包含了count和一些用来操作count的函数 而这些操作函数呢 比如说啊刚才的increment decrement reset 我们都用usgo back包裹起来了 这是一个好习惯 可以确保函数的引用稳定性 避免不必要的重渲染 在真实的应用中非常重要 然后呃首先我们测试一下 我们首先会测试它的初始状态好 这个测试的目标就是验证这个hook 能否正确的接收 并且使用我们传入的一个初始值 呃我们看啊 在这个测试用例里 我们首先调用这个render hook 并且在这个回调函数里传入了这个啊 数字十作为初始值 然后我们会进行断言 我们期望这个i result in current里面的count属性 它的值应该是十 其实非常简单直接 好初始状态状态呃 刚才测试了是一个初始状态 现在我们来呃测试更复杂的场景 就是状态更新 比如我们调用啊increment函数时 这个count值应该应该按理来说应该会加一 但在这里有一个关键点需要注意 在react里 无论是use state还是use reducer 它触发的状态更新都是异步执行的 这就意味着你不能在前脚调用了更新函数 后脚就立即断言新的状态 那样就很可能会测试失败 所以为了解决这个问题啊 呃testing library提供了一个核心工具 它叫acts act函数 你只需要记住一个原则 任何会导致hook状态更新的操作 都会包裹在act act的回调函数里 act会确保他们内部触发的所有更新 都已经处理完毕 等他执行完成之后 你再去进行调研呃 断言拿到的就一定是最新的状态 我们来看一个完整的例子 这个例子同时验证啊increment和decrement 首先我们用这个初始值零来去渲染这个hook啊 接着看这里 我们把哦i result点current 点increment调用 这个调用放到了这个ACT函数里 在act执行完毕之后呢 我们断言count应该变成一 同理我们测我们再用act去包裹decrement调用 然后再断言啊 这个count又变回了零 更进一步 在真实世界里 一个组件会因为副组件的props发生变化 而重新渲染 如果我们的hook依赖了这些prop 比如uh use count the initial state Uh initial value 我们应该如何测试这些场景呢 嗯testing library同样也为我们考虑到了 它提供了RRENDER函数 RRENDER的用法稍微复杂一些 首先他会呃在调用render hook的同时 我们除了可以拿到啊result 还可以结构解构出RRENDER函数 其次我们传递啊 传递给这个re render hook函的回调函数 需要能接收props 最后在arrana hook的第二个参数 一个配置对象 一个配置对象里面呢 我们通常哦我们要通过initial props 来提供初始的属性 这样设置好之后 我们就可以模模拟任何时候我呃我那可以安 在测试任何的时候调用这个LLANDER 并且重新传入一个新的props 来模拟一次组件的重渲染 好我们来看一个综合运用RRENDER和act的例子 这个测试的目的是啊 当这个initial value改变的时候呢 reset函数会不会啊 会不会重置到这个新的初始值 而不是旧的纸 他要做个验证 首先第一步呢我们用初始值零去渲染hook 然后我们去调用啊 Increment 让这个count变成一 好关键来了 我们会调用这个RELDER函数 并且传入新的props啊 initial value变成了十 这一步就模拟了组件的重渲染 最后在我们的act中去调用这个reset函数 此时内respect内部的依赖的initial value 应该是已经是上一上一步更新过了十了 所以我们应该会断言啊 count等于十 这个测试通过就证明我们的hook在props变更时 props更新时他的行为是正确的 好到这里 常规的hook测试其实你已经掌握了 但是面试官往往会追问一个啊更加复杂的场景 比如你如果你的户口内部有异步操作 比如fetch数据啊 该怎么测 对于异步的hook呢啊 testing library提供了啊 wait for这一类的函异步工具函数 我们来看一个看一个假设的啊 看一个假设的use fetch的例子 注意现在测试函数是异步的 首先我们呃就是渲染去渲染后hook嘛 然后啊此时 就是啊首先我们去做一个mock的调用嘛 去mock啊 模拟一个FECH请求 然后呢我们去定义完 定用render hook去定义一个hook嗯 这时候呢额我首先显而易见的 其实我们的loading状态应该是true 然后我们去额使用到这个await wait for 它的作用就是会反复的执行我们传入的断言 传入的断言 然后直到它通过或者超时 我们在这里等待这个loading的状态变成false 一旦wait for执行完毕之后呢 就说明我们的异步请求已经完成了 这时候 就我们就可以安全的对最终的data进行断言 好在掌握以上所有知识后 我们现在可以来完整的回答这道面试题了 在项目中 你如何保证自定义hook的质量和稳定性 你如你会如何对一个封装了异步请求 比如use fetch的hook进行测试嗯 当面试官问到这个问题时 我们可以分几步来回答 去展示我们的逻辑层次 首先第一步一句话点明中心思想啊 我会强调自定义 hook作为项目中逻辑复用的核心 它的稳定性至关重要 因此为他编写单元测试 是我们项目质量保障体系中必不可少的一环 然后第二步我们需要点名使用的工具啊 会说我们团队可能会统一使用这个RT l提供的 这个react hooks来进行测试 并且简单解释它的优点 就是它能够自动的创建一个隔离的测试环境 来渲染hook 让我们能专注于测试逻辑本身 然后第三步也是最核心的一步 就是分场景去描述具体的测试策略 这就能充分体现你的经验啊 对于初始状态 我们用render hook去渲染 然后直接去断言result点current 然后对于状态更新呢 我们会把触发更新的操作 比如点击调用函数等等 都会包裹在ACT里面去 确保额断延时状态已同步 对于依赖外部props的更新 我们会使用RELDER函数来模拟组件的重渲染 测试hook的响应 最后对于啊特别提到的异步逻辑啊 我们会结合a think weight和wait for的工 这样的工具函数去等待异步操作执行完毕之后 再对最终的状态和结果进行断言 并且我们会使用JUSTINMOK或者是spy on 这样的来模拟掉真实的API请求 去确保测试的独立和高效 这样一套组合拳打出来 面试官一定会对你的知识深度和广度 感到非常满意 好我们快速回顾一下今天的内容测试 自定义hook标准库 就是RTL杠啊 Rereact hooks 你需要牢牢记住它的几个核心API 首先render hook是用于渲染 然后啊result点colon用来访问结果 act用来包装包裹状态的更新 RELANDER是用来模拟重渲染以及嗯 wait for是用于处理异步的 最后最终我们测试的思想向啊一个用户一样 去关注用hook的输入和输出 而不是它的内部实现细节 这正是testing library所倡导的一个理念 好希望这一集内容能够帮你彻底的搞明白 自定义hook的测试 感谢收看 我是方格 我们下期再见
