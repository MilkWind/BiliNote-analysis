## 目录
- 面试题要求与核心思路
- 使用 Promise 实现 sleep 函数
- 使用 async/await 实现 sleep 函数
- 使用回调函数实现及不推荐原因
- AI 总结

## 面试题要求与核心思路 *Content-[00:02]
- **题目要求**：定义一个 `sleep` 函数，要求传入毫秒值，等待对应的毫秒数后再执行后续代码。
- **实现方式**：面试官通常要求分别使用 `Promise`、`Generator`（本视频暂不讲解）以及 `async/await` 来实现。
- **核心思路**：无论使用哪种方式，底层的核心都是利用 `setTimeout` 定时器来实现延迟。对于定时器这类异步代码，最佳实践是使用 `Promise` 将其包装起来，以便更好地控制执行流程。

## 使用 Promise 实现 sleep 函数 *Content-[00:18]
- **基本结构**：`sleep` 函数需要返回一个 `Promise` 对象。
- **实现细节**：
  - 在 `Promise` 的执行器函数中，编写 `setTimeout`。
  - `setTimeout` 接收两个参数：一个是回调函数，另一个是传入的毫秒值 `ms`。
  - 在 `setTimeout` 的回调函数中，调用 `resolve()` 来改变 `Promise` 的状态，从而触发后续的 `.then()` 操作。
- **代码示例**：
  ```javascript
  function sleep(ms) {
      return new Promise((resolve) => {
          setTimeout(resolve, ms);
      });
  }
  ```
- **调用方式**：
  ```javascript
  sleep(2000).then(() => {
      console.log('两秒后执行');
  });
  ```

## 使用 async/await 实现 sleep 函数 *Content-[02:26]
- **基本原理**：`async/await` 本质上是 `Promise` 的语法糖，原理与上述 `Promise` 实现相同，只是在外部再包裹一层 `async` 函数，使异步代码的编写和阅读更像同步代码。
- **实现细节**：
  - 定义一个 `async` 函数（例如 `demo`）。
  - 在函数内部使用 `await` 关键字调用 `sleep(ms)`。
  - `await` 会处理其后的表达式，将其包装/视为 `Promise` 对象进行等待，直到其状态变为 `resolved` 后才继续执行后续代码。
- **代码示例**：
  ```javascript
  async function demo() {
      await sleep(1000);
      console.log('一秒后执行');
  }
  demo();
  ```

## 使用回调函数实现及不推荐原因 *Content-[03:41]
- **实现方式**：除了 `Promise` 和 `async/await`，也可以通过传统的回调函数来实现。
  - 函数接收两个参数：毫秒值 `ms` 和回调函数 `callback`。
  - 内部使用 `setTimeout(callback, ms)` 来执行回调。
- **代码示例**：
  ```javascript
  function sleepCallback(ms, callback) {
      setTimeout(callback, ms);
  }
  
  sleepCallback(2000, () => {
      console.log('两秒后执行');
  });
  ```
- **为什么不推荐**：
  - **回调地狱隐患**：回调函数嵌套回调函数极易产生“回调地狱”（Callback Hell）问题，导致代码可读性极差。
  - **扩展性差**：虽然当前可能只有一层需求，但无法保证未来业务代码不嵌套。如果在回调函数内部还需要调用其他异步函数，嵌套层级就会不断加深。
  - **维护成本高**：一旦嵌套变深，后续回头修改和调试代码会非常困难。
  - **最佳实践**：在项目开发初期，就应该选择更友好、更现代的方式（如 `Promise` 或 `async/await`），从根源上避免回调地狱的产生。

## AI 总结
本次视频详细讲解了前端面试中常见的“自定义 sleep 函数”的实现方法。核心思路是利用 `setTimeout` 处理延迟，并推荐使用 `Promise` 进行封装。视频分别演示了基于 `Promise` 和 `async/await` 的标准实现方式，这两种方式能有效避免代码嵌套，提升代码的可维护性。同时，视频也展示了传统的回调函数实现方式，但明确指出了其容易引发“回调地狱”的缺陷，强调在实际开发中应优先采用 `Promise` 或 `async/await` 等现代异步处理方案。

---

## 文稿转写

各位同学大家好 今天我继续给大家讲解关于这道面试题 它让我们定义一个sleep函数 要求传入多少毫秒 然后呢就可以等待多少毫秒后执行啊 他们要我们分别用promise generator a sync来做generator呢 我暂时不不去讲了 我们使用分别使用promise和think来实现啊 其实核心啊就是晒太帽子 对吧啊 Set time out 然后呢我们用promise去实现 那么外壳呢函数是一个什么sleep函数 对不对 Three function Sleep 参数呢传入毫秒值 那么要想实现 啊要想实现 那么我们该怎么做 其实很简单 怎么样 我们返回一个promise对象不就可以了吗 在promise对象里面 我们去写我们的SETOUT 因为大家记住 一旦看到定时器这种异步代码 是不是最好用promise包装起来 你有一个promise对吧 然后呢 resolve函数 然后在这里面我们去写set time out 然后set time out是不是要执行一个函数 那就执行这个函数不就行了吗 然后呢时间多多长时间呢 哎参数传到ms毫秒值就可以了 这就写完了 试下效果 sleep函数睡眠两秒 延迟两秒执行 然后什么呀 是不是点DE啊 对不对 然后在这里面打印一句话 两秒后执行 来运行一下效果 是不是两后两秒后执行 这就是使用什么 使用我们的promise实现的一种方式 那还有没有他告诉我是不是用a think啊 原理是一样的 a think只不过再包一层 还是我们的promise来 function demo其实还是写我们的代码 只不过呢这回我们的sleep函数 要使用ASSIG的方式 A s y n c 参数错毫秒 然后呢这就不是return await 调用demo 把什么ms传进去就可以了 它会返回promise吧 Await 后面会把后面表达式怎么样 包装成一个promise对象 对不对 所以我们再试一下sleep 比如说这是一秒 打印一秒后执行 来我们刷新一下 是不是一秒后执行啊 那么这就是分别使用我们的promise和a think 来实现的 我们的sleep这么一个函数 当然使用回调函数可不可以呢 可以不推荐啊 不推荐也能写 来给大家写一下 function call back或者sleep吧 然后呢首先说毫秒 然后紧接着紧接着怎么样call back 然后在这里面执行一个set time out 然后call back m s 简单吧简单但不推荐啊 来试一下sleep两秒 然后 在这 是不能回的函数吧 执行写上两秒后执行 是不是也能行 为什么不推荐之前的课程 我们就讲过吧 回调函数嵌套回调函数会产生回调地域问题 尤其是如果你只有一层需求 这还好 如果说在回调函数里面还要会写其他函数 那这就是个隐患 他说老师 那我不嵌套不就完了吗 不是这么回事 你第一层既然选择了回调 你怎么能保证以后代码不嵌套呢 你你确定你就永远就这一层吗 如果说真的有以后在这里面再写函数 那是不是就嵌套深了 你再回头改代码是不是就费劲了 所以开头我们就用比较好的方式 promise或ASSIC 明白吧啊开头我们就选择比较好的 比较友好的方式去做才可以啊 这就是关于这一道面试题的一个使用
