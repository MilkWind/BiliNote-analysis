# 手写一个简化版 Promise

## 目录
- 1. Promise 核心概念与机制
- 2. 为什么面试常考手写 Promise
- 3. 手写 Promise 的核心要素
- 4. 代码实现：构建 SimplePromise 类
- 5. 使用示例与链式调用
- 6. 核心关键点与面试应对思路
- AI 总结

## 1. Promise 核心概念与机制 *Content-[00:47]

- **基本概念**：Promise 是 JavaScript 中用来处理异步操作的一种机制。在过去，开发者主要依赖回调函数处理异步，但随着异步逻辑复杂化，极易陷入“回调地狱”。
- **本质理解**：它代表了一个异步操作的最终状态（无论成功还是失败）。可以将其理解为一个“占位符”，代表在未来某个时间点才被填充的值。
- **三种状态**：
  - `pending`（待定）：初始状态。
  - `fulfilled`（成功）：异步操作完成，伴随一个成功的值。
  - `rejected`（失败）：异步操作失败，表示失败的原因。
- **状态不可逆性（核心特性）**：一旦 Promise 的状态从 `pending` 改变为 `fulfilled` 或 `rejected`，就会永远停留在该状态，不会再发生任何变化。不存在从成功变失败或从失败变成功的情况。

## 2. 为什么面试常考手写 Promise *Content-[03:07]

面试官要求手写 Promise 主要基于以下三个原因：
- **解决回调地狱**：掌握 Promise 能帮助优雅地解决回调嵌套问题。其提供的链式调用结构让异步代码的逻辑流向更加清晰易懂。
- **统一异步操作写法**：无论是处理定时器、网络请求还是文件读写，封装成 Promise 后，都可以使用统一的 `.then`、`.catch` 链式风格来组织代码。
- **简化错误处理**：通过 `.catch` 方法，可以集中处理 Promise 链中任何一个环节可能出现的错误，避免了在每个回调函数中重复编写错误检查逻辑。

## 3. 手写 Promise 的核心要素 *Content-[04:26]

实现一个简化版 Promise，核心依赖以下几个要素：
- **内部状态**：需要一个变量记录 Promise 当前的状态（`pending`、`fulfilled`、`rejected`）。
- **结果与原因变量**：需要两个变量分别存储异步操作成功时的结果（`value`）以及失败时的原因（`reason`）。
- **回调函数队列**：当 Promise 处于 `pending` 状态时，用户通过 `.then` 方法注册的成功和失败回调不能立即执行，需要先存储在回调函数队列中。
- **状态改变方法**：`resolve` 和 `reject` 方法，它们会在 Promise 构造函数中暴露给外部的执行器函数（executor），用于改变状态。
- **核心 `.then` 方法**：负责接收并注册用户提供的成功和失败回调函数。**最关键的一点**：`.then` 方法必须返回一个全新的 Promise 实例，这是实现 Promise 强大链式调用能力的基础。

## 4. 代码实现：构建 SimplePromise 类 *Content-[06:54]

### 构造函数 (Constructor)
- 接收一个 `executor`（执行器函数）。
- 在实例内部初始化 `state` 为 `pending`，`value` 和 `reason` 初始化为 `undefined`。
- 初始化两个空数组（`onFulfilledCallbacks` 和 `onRejectedCallbacks`），用于存储成功和失败的回调队列。
- 在构造函数体内定义 `resolve` 和 `reject` 方法，并传入立即执行的 `executor` 函数。

### resolve 方法
- 接收一个成功的值 `value`。
- 判断当前状态是否为 `pending`（只有在 `pending` 状态下才能转换）。
- 若为 `pending`，将状态改为 `fulfilled`，并保存 `value`。
- 遍历并执行所有存储在 `onFulfilledCallbacks` 队列中的成功回调。
- **重要细节**：根据 Promise A+ 规范，即使状态确定后执行已储存的回调，这些回调也**必须是异步执行的**。因此使用 `setTimeout(..., 0)` 来模拟微任务的异步性。

### reject 方法
- 接收一个失败原因 `reason`。
- 判断当前是否为 `pending`，若是则改为 `rejected` 并保存 `reason`。
- 遍历并执行 `onRejectedCallbacks` 队列中的失败回调（同样需要异步执行）。

### 执行器函数调用
- 在构造函数最后，立即执行传入的 `executor` 函数。
- 为了健壮性，使用 `try...catch` 包裹并同步执行 `executor`，将内部定义的 `resolve` 和 `reject` 传递给它。
- 如果 `executor` 执行过程中抛出异常，则捕获错误并调用内部的 `reject` 方法，将状态变为 `rejected`。

### then 方法（链式调用核心）
- 接收 `onFulfilled` 和 `onRejected` 两个可选参数。若未传入，则提供默认函数（成功默认透传值，失败默认抛出错误）。
- **核心**：必须返回一个新的 `SimplePromise` 实例。新实例的状态和结果由当前 Promise 状态及回调的返回值决定。
- 在新 Promise 的执行器函数内部，定义辅助函数 `handleFulfilled` 和 `handleRejected`：
  - `handleFulfilled`：使用 `try...catch` 包裹，执行 `onFulfilled` 回调并传入当前 `value`。简化版中直接调用回调的返回值来 `resolve` 新 Promise（忽略 A+ 规范中复杂的 Promise 解析过程）。若抛出异常，则 `reject` 新 Promise。
  - `handleRejected`：执行 `onRejected` 回调并传入当前 `reason`。若回调成功执行并返回普通值，新 Promise 状态变为 `fulfilled`（错误被捕获并转化为成功）；若抛出异常，新 Promise 状态变为 `rejected`。
- **状态判断与执行逻辑**：
  - 如果当前 Promise 已经是 `fulfilled` 或 `rejected`：使用 `setTimeout(..., 0)` 立即异步执行对应的 `handle` 函数。
  - 如果当前状态还是 `pending`：将包裹了 `handleFulfilled` / `handleRejected` 逻辑的匿名函数推入对应的回调队列。待未来状态确定后，由 `resolve` 或 `reject` 遍历队列执行。

## 5. 使用示例与链式调用 *Content-[18:07]

- **创建实例**：传入 `executor`，使用 `setTimeout` 模拟 1 秒延迟。延迟结束后生成随机数，大于 0.5 调用 `resolve` 模拟成功，否则调用 `reject` 模拟失败。
- **链式调用演示**：
  - 第一个 `.then`：接收成功回调，打印成功信息，并返回一个普通字符串。该返回值会作为下一个 `.then` 的成功结果。
  - 第二个 `.then`：仅提供成功回调，打印上一个 `.then` 返回的字符串。
  - `.catch`：相当于 `.then(undefined, onRejected)` 的语法糖，用于捕获链中任意一步可能出现的错误（如第一个 Promise 失败，或 `.then` 回调中抛出异常）。

## 6. 核心关键点与面试应对思路 *Content-[20:17]

### 必须牢记的关键点
1. **状态不可逆**：只能从 `pending` 转换到 `fulfilled` 或 `rejected`。
2. **回调异步执行**：即使 Promise 状态已经确定，调用 `.then` 时传入的回调也必须在下一个异步任务周期执行（通过 `setTimeout 0` 模拟）。
3. **then 返回新实例**：`.then` 方法必须返回一个新的 Promise 实例，这是实现链式调用的基石。
4. **执行器同步执行**：传给 Promise 构造函数的 `executor` 函数是会立即同步执行的。

### 面试应对思路
当遇到手写 Promise 的面试题时，可围绕以下几点组织回答：
- **概念层面**：清晰描述 Promise 的三种状态及不可逆的转换规则。
- **基础代码层面**：说明如何在类实例中维护状态、结果（`value`）和原因（`reason`）变量，以及存储回调的队列数组；说明 `resolve` 和 `reject` 的作用是改变状态并触发对应的回调执行。
- **深度讲解 `.then`**：重点讲解 `.then` 方法的实现要点，包括如何根据当前状态执行或注册回调、如何处理回调的返回值以决定新 Promise 的状态、如何使用 `setTimeout 0` 模拟异步执行，以及确保返回一个新的 Promise 实例。

## AI 总结

本视频详细讲解了前端面试中高频考点“手写简化版 Promise”的核心原理与代码实现。笔记首先明确了 Promise 作为异步操作占位符的三种状态（pending、fulfilled、rejected）及其不可逆特性。随后深入剖析了手写 Promise 的四大核心要素：状态管理、结果存储、回调队列以及返回新实例的 `.then` 方法。在代码实现部分，详细拆解了 `SimplePromise` 类的构造函数、`resolve/reject` 状态流转机制，以及利用 `setTimeout 0` 保证回调异步执行的规范细节。最后，通过链式调用示例和面试应对思路，帮助开发者不仅“知其然”，更“知其所以然”，从而在面试中展现出对 JavaScript 异步编程机制的深刻理解。

---

## 文稿转写

哈喽大家好 我是方格 今天我们来探讨一个在前端面试中非常常见 同时也非常基础的核心话题 就是手写一个简化版的promise 通过这个过程呢 我们不仅能加深对promise工作原理的理解 也能提升我们异步编程的能力 那么在本集内容 我们会覆盖以下几个要点 首先我们会深入的理解promise的机制是什么 其次我们会聊一下 为什么在技术面试中经常会被要求手写promise 最后也是最重要的 我们会一步步的从零开始 实现一个基本的promise框架 好我们先来简化的回答一下什么是promise 从最核心的概念上来说 promise是JAVASCRIPT中用来处理异步操作的一种机制 在过去我们可以可能依赖于异步函数 回调函数处理来处理异步 但是随着异步逻辑的变化 复杂化 就很容易陷入回调地狱嗯 那么更进一步的 它代表了一个异步操作的啊 最终状态 无论这个结果是成功还是失败 你可以把它理解为一个占位符 在一个在未来某个时间点才被填充的值啊 呃一个实例在他的生命周期里会处于三种状态 第一种是pending 也就是待定状态 当额异步操作完成之后呢 promise的状态就会变从pending变成full field 这个状态通常伴随着一个成功的值 而当异步操作失败时 promise的状态会从pending变成rejected 这就表示啊一一个额失败的原因 由关于这种三 这三种状态呢有一个至关重要的特性 那就是状态的不可逆性 一旦promise的状态从pending 改变为full field或者是rejected 它就永远地停留在那个状态 不会再发生任何变化 所以这状态只能是从pending到FULFIELD 或者是从pending到rejected 没有从啊成功变成失败 或者从失败变成成功的一个情况啊 额那么现在我们回到一个面试题里面 如果额面试官为什么喜欢让你去手写promise 主要有原几点原因啊 首先掌握promise 能够帮助我们优雅地解决回调地域的问题 promise提供的链式调用结构 让异步代码的逻辑流向更加清晰 而且易懂 其次呢 promise帮助我们统一了不同异步操作的写法 无论你是处理定时器啊 或者是网络请求还是文件读写 封装成promise后 我们就可以用统一的点DAN 点catch的链式风格来组织代码 最后也是一个很大的优势 promise让错误处理变得更加容易 通过点catch的方法 我们就可以集中的处理 promise链中任何一个环节可能出现的错误 就避免了在每个回调函数中重复的编写呃 错误的检查逻辑 那么理解了概念和作用后 我们来看看如何如何实现一个啊 手写一个简化版的promise 它的核心主要依赖几个元素 几个要素 首先我们要一个内部状态去记录promise 当前的状态 也就是pending full field和rejected3个值 紧接着呃 需要两个变量来分别存储 异步操作成功时的结果 value以及啊失败时的原因 Reason 好额 关键来了 当promise还在pending状态的时候呢 呃用户通过 用户通过点赞方法去注册啊 一个回调吧 就是成功和失败的回调啊 这这两个回调是并不能立即执行的 需要先存储起来 回调函数的队列 那么改变呃promise的状态呃 的一个的两个变量是由这两个方法来改变了 resolve和reject 他们会在promise构造函数中去啊 暴露给外部的执行器函数 那么最后也是最核心的方法就是啊D方法 但方法就负责接收 并且注册用户提供的成功和失败回调函数 并且氮方法最重要的一点是 它必须返回一个全新的promise实例 新全新的普罗米斯实力 所以正是因为氮方法返回了一个新的promise 我们才能实现promise强大的链式调用能力 好理论说完了 我们就进入代码部分 看看如何构建这个simple promise类 首先是我们会定义一个基本的类 定义一个simple class a simple promise 好啊 然后他的构造函数接收额一个execute 就是一个执行器函数嘛 然后呢我们在实例内部 我们初始化state是pending的状态 然后value和reason就初始化成undefined 以及两个空数组 用来存储成功和失败回调的队列呃 在这个构造函数体内呢 我们还需要定义两个方法 一个resolve 一个reject 并且传入这个立即执行函数啊 然后接接着我们来看result方法的实现啊 result方法首先他接受一个成功的值 一个value 他首先会判断当前的状态是否是pending 只有在pending状态下才能转换 如果处于pending呃 那个状态就会改成full field 并且保存这个value的值 然后呢去便利并且执行所有存储在这个on full field call back的队列中的一个成功的回调 还有这一点非常重要啊 这有一点非常重要 即使在状态确定后执行已储存的回调 那么根据这个promise a加规范 这些状这些回调也必须是异步执行的 所以呢我们就会用set time out 然后给他一个零去模拟这个微任务的异步性 好同样的我们来看看reject方法 其实reject方法它和resolve是类似的 首先他接收一个失败原因reason 同样的我们当判断当前是否是pending 如果是的话 则将这个状态改成rejected 并且保存传入的reason 紧接着呢 呃我们会去便利 并且执行所有存储在这个on rejected call back x队列中的失败回调额 这些失败回调通常同同样的也需要去异步执行 那么在构造函数的最后呢 构造函数的最后啊 我们还需要立即执行传入的这个execute函数嗯 为了健壮性 我们会用一个try catch去包裹它 然后同步执行这个executor 并且将我们内部定义的resolve和reject方法 传递给他 如果execute在执行过程中抛出了任何异常 我们就去捕获这个错误 并且调用内部的reject方法 把这个promise的状态变成rejected 呃现在来看电方法 这就是实现promise链式调用的关键 then方法接收两个可选参数 on fulfilled成功回调和UNREJECTED失败回调 而我们对我们先对这个传入的回调做一些处理 确保他们是一个是函数 或者提供一个默认的通过函数和抛出的错误啊 这里提供了一个呃默认的函数嘛 然后咳额 这里的核心就是DAN方法必须返回一个新的simple promise实例 这个新的promise的状态和结果 就将由当前的promise状态以及FULFUNFULFILLED 或者是rejected的回调的返回值来决定 我们在新的promise的执行器函数内部 来处理这些逻辑 嗯这是一个B包 新的promise和和resolve reject方法 可以在这里被调用 那么在这个新的promise执行器内部呢 我们去定义一个helper函数啊 一个handle fulfilled和handle reject方法去啊 处理回调的执行和结果 比如这个handle full field去 它是用来它是用来处理成功回调的 Unfulfid 我们同样使用这个track catch去包裹 因为用户提供的回调可能抛出异常 然后接着我们去啊执行这个回调功夫 FID的回调却传入当前的promise的成功的值额 那么在简化版本中呢 我们就直接调用回调的返回值resolve呃 呃来result来resolve成功新呃 新返回的promise呃 其实promise a加标准 在这里有更复杂的一个promise解析过程 它是用来处理回调啊 返回的pro返回promise DARIABLE对象 甚至自身的循环引用这种边界情况的 但是呃手写我们的手写板 就可以先忽略这些复杂的条件 然后咳然后如果是呃 catch就是这个unfulfilled回调呃 如果发生错误的时候呢 这里就会catch到 然后reject新的返回的promise 并且传入捕获到的错误 呃那么类似的handle rejected 就用来处理失败回调 Unrejected 那么执行这个own reject回调时呃 去我们就传入了一个当前promise失败的原因 reason嗯 这里需要特别注意 如果失败回调reject成功执行 并且返回一个普通值 那么通过D方法返回的啊 新的promise状态就会变成full field 并且这个结果就是这个返回的result 这时候呢promise链中错误被捕捉 并且转化为成功分支的 这就是啊 这是一个机制啊 错误捕捉了 但是转化成成功了 但是呢如果在执行UNRETRACTED回调时 抛出了新的异常 那么新的promise状态就会变成rejected失败 原因就是这个新的异常错误会继续向下传递 那么额接下来是氮方法 在新的promise的执行器内部呢 我们要根据当前的promise 也就是啊调用点DAN的那个实例的状态 来决定行为呃 如果当前的promise已经是fulfilled 或者是rejected 我们就直接异步执行对应的handle函数 额重点在于这 如果当前他的状态还是PDING 那么我们就不能立即执行回调 而是把额包裹了这个handle full field 逻辑的一个函数 推入到推入到当前promise的成功回调队列 这个on fulfilled call back ks里面 注意推入队列的是一个匿名函数嗯 退出队列是个匿名函数 它会它在执行时会保证handle full field 也是异步调用的 那么同样的 我们把包含handle retracted的函数推入到失败回调队列里 这样当未来啊 当前promise的状态确定后呢 resolve或者是reject方法会便利这个队列 会便利这个队列啊 并且去执行这些队列中的函数 如果调用电方法嗯 当前the promise就已经不是pending状态了 那么假如他们已经变成了FULFID啊 我们就需要立即啊 但是是在下一个宏任务或者微任务周期 去执行之前定义的handle full field diss点value 然后将这个成功值传递进去 注意这里的set time out0仍然是必要的啊 去保证了且回调的异步性 同理这个如果是rejected 就会立即异步执行这个handle reject函数 去传入失败的原因 那么这样就表保证了 无论调用D啊 无论何时去调用DAN 只要promise不是pending注册的回调 都会在下一个异步周期去执行 好我们一个大致的简化版的promise 核心逻辑就完成了 我们来看它的使用示例 我们首先建立一个新的simple promise实例 去传入了一个execute执行函数 那么在这个执行函数里呢 我们用set time out去模拟一个异步操作 比如延迟一秒 然后延迟结束之后呢 我们生成了一个随机数 一个随机数 如果随机数大于0.5 我们调用resolve却模拟操作成功 否则的话我们调用retract模拟操作失败啊 这样我们就创建了一个随机成功 或者随机失败的promise 接着我们调链式调用点DAN方法 第一个DAN接收一个成功回调 如果promise成功 这里会打印成功信息 并且呢啊这个成功回调会返回一个普通字符串 根据我们DM方法的实现 这个返回值会被作为下一个dam的成功结果 所以看第二个DET它只提供了成功回调啊 第二第二第二个点它只提供成功回调 这里就会打印出上一个呃带返回的那个字符串 最后我们再添加一个点catch 在标准的promise中 catch是D 然后接受个undefined 介绍个UNREJECTED的语法堂案 它用来捕获链中任意一部可能出现的错误 比如第一个promise失败了 或者啊第一个DAN或失败回调就抛出异常了 都会被这个catch捕获到 那么手写promise的过程中 有几个关键点需要牢记 首先我们反复强调啊 状态不可逆 就是只能从pending转换到full field或者是rejected啊 其次呢回调函数必须异步执行 即使promise状态已经确定了调用电时 它传入的回调 也应该在下一个异步任务周期去执行 我们用set up set out0去模拟这种行为 然后再次强调 then方法必须返回一个新的promise啊 它的核心就是他必须返回一个新的promise实例 这就是实现promise链式调用的基石 那么另外呢呃传给promise构造函数的 execute函数是会立即执行的啊 那么了解了这些 我们去额在面试时遇到了这个手写题的时候呢 面试官通常考察是什么嗯 首先他们会问你 他对你对promise状态的理解 以及他们之间状态规则的额状态 状态转换规则的理解啊 然后更进一步了会让你写一个简要的代码 至少实现这个constructor和这个点DAN 这两个核心部分 所以我们首先要呃回答这类似问题的思路啊 就可以围绕几点去组织 首先清晰的去描述 promise的三种状态和不可逆的转换规则 然后在代码层面呃 你需要能够说出如呃如何在类实例中维护状态 变量结果和原因 以及存储回调的队列数组 并且知道resolve和reject方法的作用是改变状态 并且触发对应的回调 执行这个啊 最后也是最能体现你理解深度的地方 是讲解DAN方法的实现要点 包括如何根据当前的promise状态 执行或注册回调 如何处理回调的返回值 决定新的promise状态如何类似呃 set time out0的方法去模拟异步执行回调 以及确保电方法返回的啊 返回一个新的promise实例 呃 总结一下 手写promise的核心在于理解和实现几点呃 promise有pending fulfilled和rejected3种状态 状态一旦从padding改变就不可逆 通过resolve或者reject方法来驱动状态的转换呃 D方法负责注册成功和失败回调 并且关键在于他返回了一个新的promise 从而实现链式调用 最后promise规范要求 回调函数必须在下一个异步任务周期执行 即便是在promise状态已确定的情况下 这点要通过异步手段来保证好的 以上就是关于手写一个简化版 promise的全部内容 希望通过今天的讲解呢 大家对promise的内部机制有更清晰的认知 也能在面试中自信地展示这部分的知识理解 感谢大家的收看 我是方格 我们下期再见
