## 目录
- [1. async/await 是什么](#1-asyncawait-是什么)
- [2. 为什么使用 async/await](#2-为什么使用-asyncawait)
- [3. 基本 API 和用法](#3-基本-api-和用法)
- [4. 核心注意事项](#4-核心注意事项)
- [5. 总结回顾](#5-总结回顾)
- [AI 总结](#ai-总结)

## 1. async/await 是什么 *Content-[01:16]

- **概念定义**：`async` 和 `await` 是 JavaScript 中处理异步函数的一种现代语法糖。
- **语法糖本质**：它们本身并没有引入新的底层能力或模型，而是通过更简单、友好的语法，让开发者能够以类似同步代码的方式去书写异步逻辑。
- **底层基础**：并非空中楼阁，而是坚实地构建在 JavaScript 现有的异步基础之上，特别是 `Promise` 以及早期的 `Generator`（生成器）。其底层实现很大程度上借鉴并优化了 Generator 的暂停和恢复机制。
- **核心作用**：允许在 `async` 函数内部暂停当前函数的执行，等待一个 `Promise` 的决议（即进入 `fulfilled` 或 `rejected` 状态）。一旦 `Promise` 决议完成，函数就会恢复执行，并根据状态获取决议的值或捕获抛出的错误。

## 2. 为什么使用 async/await *Content-[03:02]

尽管 `async/await` 只是语法糖，但它带来了显著的额外价值：

- **提升代码可读性**：与传统的 `.then()` 链或早期的回调函数相比，使用 `async/await` 编写的异步代码执行流程看起来更像习惯的同步代码，一步一步往下走。这极大地改善了代码的线性流程感，使理解复杂的异步操作和顺序依赖变得更容易，有效避免了“回调地狱”或“Promise 链地狱”。
- **错误处理更直观**：在 `async` 函数内部，可以直接使用标准的 `try...catch` 语句来捕获由 `await` 等待的 `Promise` 拒绝所抛出的错误。这与处理同步代码抛出异常的方式完全一致，写起来和读起来更加自然。
- **更好的调试体验**：`async/await` 的调用栈通常更加简洁。当异步代码出错时，能够提供更清晰的调用栈信息，更容易定位到是哪一步的 `await` 出错以及它的调用路径，从而极大提高调试效率。

## 3. 基本 API 和用法 *Content-[05:01]

### `async` 关键字
- 当你需要在函数内部使用 `await`，或者希望这个函数总是返回一个 `Promise` 时，就需要使用 `async` 关键字来声明该函数。

### `await` 关键字
- **核心功能**：只做一件事——等待。
- **上下文限制**：只能在 `async` 函数体的内部出现。如果在非 `async` 函数中使用，会触发语法错误。
- **暂停机制**：当 `await` 后面跟一个 `Promise` 时，`async` 函数的执行会在这里**暂停**（注意：是暂停当前函数，而不是阻塞整个 JavaScript 线程）。控制权会交还给事件循环（Event Loop）。当被等待的 `Promise` 决议后，事件循环会安排该函数从暂停的地方恢复执行。
- **非 Promise 值处理**：如果 `await` 后面跟的不是 `Promise` 而是一个普通值（例如数字 `10`），`await` 不会暂停函数执行，而是立即解析该非 `Promise` 值本身。这等同于 `await Promise.resolve(10)`，等待过程是瞬间完成的。

### 实际开发场景示例（使用 fetch API 获取数据）
```javascript
async function fetchData(url) {
  try {
    // 1. 发起网络请求，返回 Promise
    const response = await fetch(url); 
    // 函数在此暂停，等待网络请求完成并收到响应
    
    // 2. 解析 JSON 数据，response.json() 也返回 Promise
    const data = await response.json(); 
    // 函数再次暂停，等待 JSON 数据完全解析
    
    // 3. 两个 await 都完成后，继续执行
    console.log(data);
    return data; 
    // 注意：即使返回普通对象 data，由于是 async 函数，返回值会自动封装在成功解析的 Promise 中
  } catch (error) {
    // 捕获网络错误、接口错误或 JSON 解析失败
    console.error(error);
    throw error; // 重新抛出错误，使 fetchData 返回的 Promise 变为 rejected
  }
}

// 外部调用处理
fetchData('https://api.example.com/data')
  .then(data => console.log('Done', data))
  .catch(err => console.error('Failed', err));
```

## 4. 核心注意事项 *Content-[11:54]

### 4.1 使用范围限制 *Content-[12:01]
- `await` 关键字**只能在 `async` 函数内部使用**。
- 如果在普通函数或顶层作用域（如 JS 文件最外层）直接使用 `await`，会导致语法错误（除非当前运行环境支持 Top-level await）。`await` 只能暂停它所在的那个 `async` 函数。

### 4.2 非阻塞特性 *Content-[12:37]
- **重要概念澄清**：`await` 关键字**不会阻塞整个 JavaScript 主线程**。
- 它仅仅是暂停当前 `async` 函数的执行，并将控制权交还给 JavaScript 的事件循环（Event Loop）。
- 这意味着当 `async` 函数在等待 `Promise` 时，主线程并没有闲着，它可以继续执行其他任务，如处理用户界面事件、运行定时器或执行其他非异步代码。理解这一点对于避免写出阻塞 UI 的代码至关重要。

### 4.3 顺序执行与并发执行 *Content-[13:24]
- **默认顺序执行**：`await` 的默认行为是顺序执行。如果有多个 `await` 表达式，它们会按照代码书写顺序依次执行，只有前一个 `await` 等待的 `Promise` 决议后，下一个才会开始。这适用于后一个任务依赖前一个任务结果的情况。
- **并发执行**：如果多个异步任务之间没有直接依赖关系（如同时请求两份不同的数据），采用默认的顺序 `await` 会浪费时间。
  - **正确实现并发的步骤**：
    1. **创建任务**：先调用返回 `Promise` 的函数，将这些 `Promise` 对象存起来（不要立即 `await`），让请求同时发起。
    2. **使用 Promise.all / Promise.allSettled**：
       - `Promise.all()`：数组中所有 `Promise` 都成功时才 resolve；任意一个 reject 则立即 reject。
       - `Promise.allSettled()`：等待所有 `Promise` 都决议（无论成功或失败），返回描述每个结果的对象数组。
    3. **统一 await**：对 `Promise.all()` 返回的 `Promise` 使用 `await`。这样 `async` 函数只会暂停一次，等待并发任务全部完成。
  - **并发示例**：
    ```javascript
    async function concurrentFetches() {
      // 立即调用 fetch，发起并发请求，不立即 await
      const promise1 = fetch('/api/data1');
      const promise2 = fetch('/api/data2');
      
      // 将 promise 放入数组，使用 Promise.all 并 await
      const [result1, result2] = await Promise.all([promise1, promise2]);
      
      console.log('所有并发任务完成', result1, result2);
    }
    ```

### 4.4 错误处理机制 *Content-[19:23]
- 如果在 `async` 函数内部，一个由 `await` 等待的 `Promise` 被拒绝（rejected），且没有被当前的 `try...catch` 捕获，错误会向上冒泡，表现为该 `async` 函数返回的 `Promise` 被拒绝。
- 如果调用处也没有使用 `.catch()` 来处理这个返回的 `Promise`，最终会导致**未捕获的 Promise 拒绝**（Unhandled Promise Rejection），这通常会导致程序报错并中断。
- **最佳实践**：始终建议在 `async` 函数内部使用 `try...catch` 来捕获可能由于 `await` 导致的错误，或者在调用 `async` 函数时使用 `.catch()` 方法处理返回的 `Promise` 拒绝。

## 5. 总结回顾 *Content-[20:41]

- **本质**：`async/await` 是 JavaScript 异步编程的语法糖，底层依赖 `Promise` 和 `Generator`。
- **优势**：通过让异步代码形式同步，极大提升了代码可读性，并与 `try...catch` 无缝配合进行错误处理。
- **核心机制**：在 `async` 函数内部遇到 `await` 等待 `Promise` 时，暂停函数执行，将控制权交还给事件循环，等待 `Promise` 决议后再恢复执行。
- **关键注意点**：
  1. `await` 必须在 `async` 函数中使用。
  2. 它不阻塞主线程，只是暂停当前函数。
  3. 默认是顺序执行；若要并发，应先创建所有 `Promise`，然后使用 `Promise.all` 去统一 `await` 结果。
  4. 不要忘记使用 `try...catch` 或 `.catch()` 来处理可能的错误。

## AI 总结

本视频深入解析了 JavaScript 中 `async/await` 的底层运行机制。作为基于 `Promise` 和 `Generator` 的语法糖，`async/await` 极大地优化了异步代码的可读性与调试体验，使异步逻辑能够以同步的方式线性书写。视频详细讲解了其核心 API 用法，并通过 `fetch` 实例演示了数据获取与错误捕获的完整流程。此外，重点澄清了 `await` 仅暂停当前函数而不阻塞主线程的非阻塞特性，对比了顺序执行与基于 `Promise.all` 的并发执行场景，并强调了规范化错误处理（避免 Unhandled Promise Rejection）的重要性。掌握这些底层逻辑与注意事项，有助于前端开发者编写出更高效、健壮的异步代码。

---

## 文稿转写

Hello 大家好 欢迎回到我们的前端小课堂 我是方格 在现代JVK开发中 处理异步操作已经变得非常非常重要了 而a sync function和await 这两个关键字 正是帮助我们更优雅 更直观地书写异步代码的强大工具 那么它们藏在语法堂之下的底层机制 究竟是怎样的呢 await真的会阻塞你的代码吗 并发异步又该应该如何使用a sync和weight 来实现呢 在本期的分享中 我们就来一起深入的探讨 a sync和weight的底层运行机制 在今天的分享里 我们首先会明确a think和weight是什么 他们在义务编程中扮演的角色 接着我们会探讨 为什么它能显著提升异步代码的可读性 当然实操是必不可少的 我们会讲解如何正确的使用a think和await 这两个关键字 最后也是非常重要的 我们会深入分析a think和weight 一些核心的注意事项 比如它的非阻塞特性 以及如何处理顺序和并发任务 以及它的错误处理机制 首先我们来明确a thing和weight是什么 从概念上来讲 a think of weight是啊 JASCRIPT中处理异步函数的啊 一种现代语法糖 所谓语法堂啊 就是它本身并没有引入底层的能力或者模型 而是通过更简单更友好的语法 让我们能用看起来像更同步代码的方式 去书写异步逻辑 那么语法堂这个语法堂是基于什么构建的呢 它并不是空中楼阁 而是坚实的经构建在JAVASCRIPT现有的业务基础上 特别是promise 以及早期用于构建promise和异步迭代的呃 generators生成器 他们在底层的实现很多 很大程度借鉴 并且优化了generator的暂停和恢复机制 所以a think和weight的核心作用是什么 很简单 它允许你在一个啊异步函数的内部 ACCEL函数的内部暂停当前函数的执行 然后等待一个promise的决议 一个result 也就是等待这个promise进入到fulfilled 或者是rejected状态 一旦promise决定了这个状态 a sync就会恢复执行 并且根据promise的状态 要么拿到它决定的值 要么抛补货 抛出的错误 那么既然a think和wait只是语法糖 那为什么我们还要用它呢 它带来了哪些额外的价值 那么第一点 也就是最显著的一点是代码的可读性啊 和传统的promise点DE啊 或者更早的回调函数相比 使用a sync和weight去写异步代码 它执行的流程看起来更像是我们习惯的同步 代码 一步一步地往下走 这就极大地改善了代码的线性流程感 使得理解复杂的异步操作和顺序呃的依赖 变得更加容易 有效的 避免了所谓的回调地域或者是promise链地狱 然后第二点是啊 第二点是他的他让错误的处理更加直观 在ACCEL函数内部 你可以直接使用标准的track catch语句 来捕获由await等待的promise 拒绝所抛出的错误 这与我们处理同步代码 抛出异常的方式完全一致 写起来和读起来就更加自然了 然后额第三点 它提供了更好的调试体验 a sync和weight的调用站 通常AASINC和weight的调用站会更加简洁吗 这就意味着呃 在使用哦a think和weight编写异步代码时 能够提供更清晰的调用栈信息啊 当你的异步代码出错时 就更容易的去定位到是哪一步的await出错了 以及它的调用路径是怎样的 就极大地提高了调试的效率 那么接下来我们看一下a think 方CTION和await的基本API和用法 首先是a think关键字 当你需要在函数内部使用await时 或者希望这个函数总是返回一个promise 就需要用到a sync这个关键字来声明它呃 关键记住啊 然后是await 就关键字嗯 await关关键字只做一件事 就是等待 但是它有一个非常重要的上下文限制 await关键字只能在呃呃think函数体的内部出现 如果非assign函数使用了await 会触发一个语法错误 当await后面跟一个promise时 AS函数的执行在这里就会暂停 请注意暂停啊 是暂停当前ACCEL函数 而不是阻塞整个JAVASCRIPT线程 他的控制权其实会交还给事件循环 当被等待的promise决议成功或者失败后 事件循环会安排这个暂停的assign函数 从暂停的地方恢复执行 如果promise成功解析 也就是resolve await求个值 求值的结果就是promise点resolve那个值 那么如果啊如果await后面跟的不是一个跟的 不是一个promise呢 而是一个普通值呢 比如说我await一个数字十 在这种情况下啊 await不会暂停函数的执行 他会立即解析那个非promise值本身 这就像是await promise resolve那个值 然后立即等待他resolve一样 因为promise的result返回的是一个立即result的promise 所以等待过程是瞬间的瞬时的好 我们来看一个经典的实际开发场景 使用a think和weight来通过fetch API获取数据 我们定义了一个fetch data函数 并且用a sync函这个关键字来标记它 在函数体内部呢 我们用一个track catch 这个快去包裹核心的逻辑 这是为了优雅的处理异步操作可能出现的问题 首先第一步我们调用这个fetch url fetch函数会返回一个promise 它代表网络请求的结果 我们紧接着使用了await这个关键字 这时候呢fetch data的执行就会在这里暂停 等待fetch返回的promise决议 也就是等待网络请求完成 并且收到响应投呃 一旦决一旦promise决议了 就是比如服务器返回了响应函数 就会恢恢复执行 呃这个await fetch url的结果也就是resolve的值 就是这个response对象包含了啊 这个响应响应的信状态码 头部信息等等 拿到这个problem response对象后 我们就调用它的JSON方法啊 因为i response and JSON也会返回一个promise 它代表了从响应题中解析 JSON数据的一个异步过程 所以我们这里再次使用await 等待这个新的promise决议 也就是等待JASON数据被完全解析出来 当这个promise也有结果之后呢 啊await这response点JASON的结果就是解析好了 这个data也就是一个对象或者数组呃 呃只有当上面两个await都完成之后呢 代码才会继续执行到data这一行 打印最终的数据 最后呢函数会返回这个data啊 请记住这里即使返回的是一个啊普通的对象data 由于fetch data是一个a sync函数 它的返回值呢就会自动的封装在一个啊 成功解析的promise中 如果呃就在这个catch快和try这个快里面 任何一个await等待的promise被rejected 比如说你可能出现了网络错误或者是接口错误 或者JASSON解析失败 那么这个错误就会被立即的捕捉 跳转到catch块去执行 那么在catch块里呢 我们就可以去处理错误 比如打印错误信息 并且可以重新选择through路出 这个错误 这时候我们最外层的SC函数fetch data啊 就那个返回那个promise就会被标记成拒绝 Rejected 他拒绝的原因就是这个error对象 然后在呃函数的外部呢 虽然我们使用了这个a think await 去简化了一个外部的内部的逻辑啊 但是啊但是我们呃调用as think函数本身 它返回的依然是个promise 所以我们依然可以通过传统的点DAN或者点catch 方法去处理啊 异步ass函数返回的promise的最终结果 好哎 就如果这个额额ASSIN函数啊 有所有的await 所有的await都返回成功之后呢啊 并且这个函数正常返回了 那么这里的点done就会被执行 接收到这个函数返回的那个值 并且被封装到这个pro啊 resolve这个promise的resolve里面 而如果这里啊函数那那一个await被拒绝了 或者在我们就会在catch里面重新抛出错误 这时候点catch就会被执行捕获到那个错误 所以通过这个例子 我们可以看到a sina weight是一种协同的方式 以一种协同的方式去一步一步的处理异步函数 异步操作 并且通用过用一些熟悉的try catch来处理错误 额虽然a think of weight用起来很方便 但是在实际的使用中 有几个非常关键的点 我们需要注意 第一个也是经常犯的错误啊 await只在关键字 只在a think函数内部使用 如果你在一个普通的函数或者顶层作用域 比如一个JS文件的最外面直接使用await 会导致一个语法错误 除非这个环境是顶层支持await的 所以记住啊 await只能暂停在它所在的那个呃think函数里面 然后第二点啊 这是一个非常重要的概念啊 上的一个澄清啊 await关键字并不会阻塞整个JAVASCRIPT主线程 它仅仅是暂停在当前assign函数的执行 并且将这个控制权交还给JAVASCRIPT的事件循环event loop 这就意味着当一个think函数在等待一个promise时 主线程并没有闲着 他可以继续执行其他任务 比如处理用户界面事件 运行定时器或者执行其他非异步代码 那么理解这一点 就是对于避免写出阻塞UI的代码是至关重要的 然后第三点要注意 await的默认行为是顺序执行的 如果你有多个多个表达式 多个wait表达式 他们就会按照代码的书写顺序依次执行 只有前一个await等待的promise决议后 下一个await才会开始执行 我们来看一个顺序执行的例子 这里有一个think函数叫sequence Sequential featues 代码高亮呃 首先打印第一条信息嗯 然后这里这里就开始获取数据嘛 然后AAWAIT去获取第一个数据杠API杠data1 那么函数就会在这里暂停 等待第一个异步请求去完成 只有当这个API的数据成功获取 也就是promise resolve后 函数才会恢复执行 打印出data a1 获取完成 紧接着打印开始获取data2啊 然后await获取第二个数据杠API杠data2 注意这个请求发送的是第一个请求完全完成 并且处理后才开始的 只有当这个杠API杠data a2也成功获取后 才会打印 Data a2 获取完成 最后打印这两个结果 这种顺序执行的方式啊 这是一个顺序执行的方式 它就适用于后一个任务 依赖前一个任务结果的一个情况 好 那但是如果两个异步任务之间没有任何 没有直接的依赖关系 比如同时请求两份不同的数据 默采用默认请求顺序的一个weight就会浪费时间 我们希望它能够并发执行 也就是同时开始要使用并发执行呢 我们就不能使用连续的await 正确的做法 第一步 首先要创建 并且并额需要并发执行的一个promise任务 也就是先调用那些返回promise的函数 把这些promise对象都存起来 然后第二步使用promise点all 或者promise点all settle 这些方法来等待所有这些promise都决议 promise点or 会在一个数组中的所有promise都成功时 才RESURESOLVE 如果任意一个promise拒绝 他就会立即拒绝promise点 OSATO呢则会等待所有promise都决议 无论是成功还是失败啊 他之后会返回一个描述每个promise 结果的对象数组 然后第三步对promise点or或者promise点 All settled 这返回的promise使用await 这样的话a single函数就只会在这里暂停一次 等待那些可以并发啊 并发方式并且开始执行的promise数组去执行 完成 我们来看使用promise点or实现并发的例子 首先定义一个a sync函数 Concorn featues 然后啊打印开始显显示信息嗯 这里啊 然后代码这这然后注意啊 这里我们没有立即await 我们调用了立即调用了fetch函数 两次分别发起了两个异步请求 那么这两个函数调用就会立即返回 两个promise对象 并且这两个promise所代表的网络请求 几乎是同时开始的 那么这就是并发的起点 然后接着呢 我们会把这两个promise都放在一个数组里面 并且作为参数传给promise点 All 然后promise点all就会返回一个啊一个数组 一个呃 新新的promise 我们会对这个promise啊去做一个await 这时候呢这个函conquent fetches 这个整额主函数体就会暂停等待promise点all 等待什么 等待promise all返回promise的状态决议 而promise点O 这个等待过程是等待它内部的数组 所有的promise都成功地返回状态 这意味着这个函数只会暂停一次 等待同时进行的两个请求都完成 当promise点all的promise成功啊 这状态是成功时 它就它的结果是个数组 会包含原先promise数组中 每个promise成功解决的一个值 这里通过一个数组结构去赋值 给了result1和result2 只有当promise点all全部啊 等待的所有并发任务都完成之后呢 代码才会继续执行打印完整的信息 最后打印结果就是通过先发并发 并行发起promise 然后再统一await promise点all啊 我们就可以高效地实现一个并发 去显著的减少总的等待时间 还有最后一个重要的注意事项是关于错误处理 就像我们前面在代码示例中看到的 如果在AS函数内部 一个由await等待的promise被拒绝了 并且这个拒绝并啊 没有被当前a sign函数内部的try catch获取 那么这个错误会向上冒泡 表现为这个assign函数返回了promise被拒绝啊 如果调用的地方也没有啊 使用点catch来处理 这个assign函数返回的那个拒绝的promise 那么他最终会变成一个未捕获的promise 拒绝也就叫一个常见的空气来炮座啊 叫unhandled promise rejection 这通常导致程序报错并且中断 所以我们始终建议在a thing函数内部 使用track catch 来捕获可能由于AAWAIT导致的错误 或者在调用extinct函数的点catch方法 去处理它返回的promise的拒绝 好我们快速回顾一下今天的核心内容 首先a sync await是JAVASCRIPT异步编程的语法堂 它底层依赖prose promises和generators 它通过异步代码形成啊形式同步 极大地提升了代码的可读性 并且和try catch无缝配合去做错误处理 它核心机制是在think函数内部遇到await promise时 暂停函数执行 然后将控制权交还给事件循环 等待promise决议后再恢复执行 所以使用a think和weight务必记住 必须await必须在assign函数中 它不阻塞主线程 只是暂停当前的函数 默认的ACCEAWAIT是顺序执行的 如果要并发 应该先创建所有promise 然后使用promise点all去等待 在await结果同时呢 不要忘记使用try catch或者是点catch 来处理可能的错误 那么理解了上面这些 a think of way的这些底层的逻辑和注意事项 你就可以更自信的在你的JASCRIPT项目中 运用它们去写出更简洁更健壮的异步代码啊 今天的分享就到这里 希望大家能有所收获 我是方格 我们下期再见
