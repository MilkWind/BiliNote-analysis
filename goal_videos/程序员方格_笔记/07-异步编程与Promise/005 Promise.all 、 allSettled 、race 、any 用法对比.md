## 目录
- 1. 引言与 Promise 静态方法概述
- 2. Promise.all 详解
- 3. Promise.allSettled 详解
- 4. Promise.race 详解
- 5. Promise.any 详解
- 6. 使用注意事项与场景对比总结
- AI 总结

## 1. 引言与 Promise 静态方法概述 *Content-[00:01]
- **Promise 静态方法简介**：Promise 对象不仅拥有 `.catch`、`.then` 等实例方法，作为类，它还提供了强大的静态方法，专门用来处理可迭代的 Promise 集合。
- **核心功能**：接收一个 Promise 的可迭代对象（例如一个 Promise 数组），然后返回一个新的 Promise。
- **核心区别**：这些静态方法之间的主要区别，体现在如何根据输入 Promise 的成功或失败，来决定自身返回的 Promise 最终的状态和结果。
- **为什么需要这些方法**：在 Web 开发中，经常会同时发起多个后端请求或并行执行多个异步任务。如果手动管理每一个 Promise 的状态（使用大量嵌套的 `.then` 或复杂的计数器来判断任务是否完成），会让代码变得非常难以维护。`Promise.all`、`Promise.allSettled`、`Promise.race` 和 `Promise.any` 提供了一种声明式、更简洁的方式去处理常见的并发场景。

## 2. Promise.all 详解 *Content-[02:45]
- **核心逻辑**：等待所有输入的 Promise 都成功执行完毕（进入 `fulfilled` 状态），或者任意一个失败。
- **成功情况**：如果输入的所有 Promise 都成功解决，`Promise.all` 返回的 Promise 会变成 `resolved` 状态。结果是一个数组，包含所有输入 Promise 成功后的值。**特别注意**：数组中值的顺序严格按照输入 Promise 数组的原始顺序排列，与实际完成的先后顺序无关。
- **失败情况（Fail Fast）**：如果任意一个输入的 Promise 失败，`Promise.all` 返回的 Promise 就会立即变成 `rejected` 状态。拒绝原因即为第一个失败的 Promise 的拒绝原因。一旦有失败，它就不会再等待其他 Promise 的结果，因此被称为“快速失败（Fail Fast）”。
- **示例 1（成功）**：定义一个已解决的 Promise、一个非 Promise 的数值（如 42，会被自动当作 `Promise.resolve(42)` 处理）、一个模拟异步延迟后解决的 Promise。将它们作为数组传给 `Promise.all`，最终 `.then` 回调会被执行，并按 1、2、3 的原始顺序打印输出。
- **示例 2（失败）**：包含一个成功的 Promise、一个立即失败的 Promise、一个延迟后会成功的 Promise。由于立即失败的 Promise 触发了 Fail Fast 机制，整个 `Promise.all` 立即返回 `rejected` 状态，通过 `.catch` 捕获到该错误原因。即使稍后有 Promise 会成功，其结果也会被忽略。

## 3. Promise.allSettled 详解 *Content-[07:01]
- **核心逻辑**：与 `Promise.all` 不同，它不会因为某个 Promise 的失败而立即终止。它会耐心等待所有的输入 Promise 都达到 `settled` 状态（即 Promise 已经结束其生命周期，无论成功还是失败）。
- **返回状态**：`Promise.allSettled` 返回的 Promise 总是会变成 `resolved` 状态（除非输入的可迭代对象本身为空，结果为空数组）。
- **结果结构**：结果数组中的每一个元素都对应输入数组中相应位置 Promise 的最终结果。元素不是 Promise 成功后的值本身，而是一个包含最终状态信息的对象：
  - 如果 Promise 成功：对象包含 `status: 'fulfilled'` 和 `value` 属性（包含成功的值）。
  - 如果 Promise 失败：对象包含 `status: 'rejected'` 和 `reason` 属性（包含失败的原因）。
- **示例**：传入一个成功的 Promise 和一个延迟后失败的 Promise。等待两个 Promise 都完成后执行 `.then` 回调。遍历结果数组打印每个结果的状态，会显示 `fulfilled` 和 `rejected`。即使有失败，依然能拿到关于结果的信息，不会中断整个流程。
- **适用场景**：非常适合执行一组相互独立，但需要知道所有任务最终结果的场景。

## 4. Promise.race 详解 *Content-[09:38]
- **核心逻辑**：顾名思义是“竞速”。它不像 `all` 或 `allSettled` 那样关心所有 Promise 的最终命运，只等待第一个改变状态的 Promise。
- **返回状态**：`Promise.race` 返回的 Promise 的状态及其结果，与第一个改变状态（跑得最快）的 Promise 完全一致。
- **示例**：Promise1 在 500ms 后解决（值为 'one'），Promise2 在 100ms 后解决（值为 'two'）。将它们传给 `Promise.race`。因为 Promise2 延迟更短，先改变状态，所以 `Promise.race` 返回的 Promise 会以 Promise2 的状态和值（'two'）来 resolve。即使 Promise1 稍后也会 resolve，其结果已被忽略。
- **适用场景**：非常适合用来实现超时控制。可以让目标任务与一个在一定时间后 `rejected` 的 Promise 去竞速，一旦代表超时的 Promise 先拒绝了，就知道目标任务超时了。

## 5. Promise.any 详解 *Content-[11:09]
- **核心逻辑**：意味着“任何一个”。专注于在输入的 Promise 中找到第一个成功解决（`fulfilled`）的 Promise。对于失败的 Promise，只要还有其他 Promise 没有完成且有可能成功，`any` 就会直接忽略这些失败。
- **成功情况**：如果输入的 Promise 数组中至少有一个最终成功解决，`Promise.any` 返回的 Promise 就会变成 `resolved`，其值就是那个第一个成功解决的 Promise 的值。
- **失败情况**：只有在一种情况下，`Promise.any` 返回的 Promise 会变成 `rejected`，那就是所有 Promise 都最终失败。
- **聚合错误（AggregateError）**：全部失败时，它不会简单地抛出最后一个失败的原因，而是会抛出一个特殊的错误类型 `AggregateError`。这个聚合错误对象包含一个 `errors` 属性（数组），收集了所有输入 Promise 拒绝的原因。
- **示例 1（成功）**：Promise1 立即失败，Promise2 延迟 100ms 成功（值为 'quick'），Promise3 延迟 500ms 成功。Promise1 失败被忽略，Promise2 在 100ms 后成为第一个成功的 Promise，最终 resolve 的值为 'quick'。
- **示例 2（全失败）**：Promise4 和 Promise5 都是立即失败的。传给 `Promise.any` 后，因为所有输入的 Promise 都失败了，返回的 Promise 变成 `rejected` 状态并被 `.catch` 捕获。打印出的错误是一个 `AggregateError` 实例，通过 `error.errors` 属性可以访问到包含所有拒绝原因（如 ErrorA 和 ErrorB）的数组。
- **适用场景**：适合从多个可能的来源（例如多个 CDN 地址）去获取资源，只要有一个成功就行。

## 6. 使用注意事项与场景对比总结 *Content-[14:20]
- **使用注意事项**：
  - 如果输入的可迭代对象包含非 Promise 的值，它们会被 `Promise.resolve` 立即包装成一个已解决的 Promise 来处理。
  - 再次强调 `Promise.all` 的 Fail Fast 特性：只要有一个失败，整体立即失败，不再关心其他结果。这在需要所有依赖都成功才能继续初始化的流程中非常高效。
- **场景对比总结**：
  - **`Promise.all`**：所有成功才成功，一个失败就失败。
  - **`Promise.allSettled`**：围观到底，等待所有完成，并给出每个结果的详细报告。
  - **`Promise.race`**：谁先到谁说了算，第一个成功或者失败决定最终的结果。
  - **`Promise.any`**：任意一个成功就成功，只要有一个成功状态就会返回成功，除非所有的都失败了才会报错，且抛出的是聚合错误类型。

## AI 总结
本视频详细讲解了 JavaScript 中用于处理并发异步操作的四个核心 Promise 静态方法：`Promise.all`、`Promise.allSettled`、`Promise.race` 和 `Promise.any`。`Promise.all` 适用于需要所有任务都成功的场景，具备 Fail Fast 特性；`Promise.allSettled` 适用于需要获取所有任务最终状态（无论成败）的独立任务场景；`Promise.race` 适用于超时控制等只需首个结果的竞速场景；`Promise.any` 则适用于多数据源容错获取，只要有一个成功即可，全部失败时抛出 `AggregateError`。掌握这些方法的差异与适用场景，能够极大提升前端异步编程的代码质量与可维护性。

---

## 文稿转写

哈喽大家好 欢迎回到方格的小课堂 今天我们将聚焦于JAVASCRIPT中 promise提供的一些非常实用的静态方法 它们能够帮助我们更高效地去处理 多个并发的异步操作 那么在本集里呢 我们会一起一起探讨一下几个关键点 首先回顾前端异步编程中 我们常会遇到哪些难题 接着我们会深入了解这四个promise静态方法哦 promised点or osettled race和any 他们是如何帮助我们编排多个promise的 并发执行的 最后我们会详细地对比它们的用法和核心差异 以便大家在实际开发中能够选择最合适的工具 好promise这个对象不仅自身拥有点catch点 DAN这样的一个方法实例 它作为一个类 还提供了一些强大的静态方法 用来处理可迭代的promise集合 首先promise的啊 这些静态方法的核心功能在于接收一组 接收一个promise的可迭代对象 比如一个promise数组 然后返回一个新的promise 它们之间的主要区别就体现在 如何根据输入的promise 成功或者失败来决定自身返回的promise 最终的状态和结果 啊那么我们为什么需要这些方法呢 想象一下 在web的开发中 我们经常会同时发起多个后端请求 或者并行的执行多个异步任务 如果手动的去管理每一个promise的状态啊 用大量的嵌套的点单 或者复杂的计数器来判断所有任务是否完成 这无疑会让代码变得非常难以维护 而promise点all assettled race和any 这些工具呢正是为解决这些问题而产生的 他们就提供了一种声明式的 更简洁的方式去处理这些常见的并发场景 首先来看promise 点all啊 它 呃他的逻辑相对直接 它会根据你等待你所输入的所有promise 都成成功执行完毕 也就是进入fulfill的状态 或者如果 但是如果输入的promise中有一个失败了呃 那么promise点all 本身返回的promise就会立即失败啊 如果promise啊输入的所有promise都成功解决 那么promise点or返回了 promise就会变成resolve状态 它的结果就会是一个数组 这个数组就包含了所有输入的promise 成功后的值 那么特别注意的是啊 这个数组这个数组的原始顺序啊 他他的值的顺序会按照你啊 严格按照你输入promise数组的原始顺序去排列 这跟他们实际完成的先后顺序是没有关系的 而如果任意一个任意一个输入的promise失败了 promise点O返回的promise 就会立即变成reject状态 他的拒绝原因呢 就是第一个失败的那个promise的拒绝的原因 这就是promise点or 常被称为啊fair fast的一个啊原因了 因为一旦有失败 他就不会再等待其他promise的结果 所以是快速失败 我们再来看一个具体的例子 这是MDN上的一个经典的例子 我们定义了三个值 首先是一个已经解决的promise 好和一个非promise的数值 以及一个模拟异步延迟后解决的promise 注意这里的数值42 当你作为输入给promise点二时 会被自动当做promise点resolve42来处理 我们把这三个数组 三个promise作为数组去传给promise点all哦 那么因为他们最终都会成功解决 所以点D的回调也被执行 这个consulted log也会被按预期的去打印出来 并且呢他们的输输出其实顺序是一致的 按123的顺序去输出 那么我们再来看一下一个失败的例子 这里我们有一个成功的promise啊 一个失败的promise Promise5 以及一个以及一个延迟后会成功的一个promise 叫promise6 我们将这三个promise 传入到这个promise点all里面 由于promise5会立即失败 他就会啊处发触发promise点 ORDFAREFAST的机制 整个promise点all 由于他的失败会立即返回reject状态 并且通过点catch去捕获到这个状态 捕获到这个错误状态 那么打印出了这个错误原因 也就是promise5拒绝的原因 所以即使这个promise6在稍后会成功 他的结果也被忽略掉了 接下来是promise点all settle 这个方法与promise点or不同 它不会因为某个promise的失败而立即终止 他会耐心的等待 所有的输入额的promise都达到settle的状态 那么settle呢就意味着啊 promise的已经结束了它的生命周期 不管promise还是成功还是失败啊 都是已经结束生命周期了 promise点OSETTLE返回的promise啊 总是会变成resolve的状态 除非输入的可迭代对象本身是空的 它的结果是个空数组 这个数组中的每一个元素都对 都对应输入数组中相应位置 promise的最终结果 这个结果 数组中的元素不是promise成功后的值本身 而是一个包含了这个promise 最终状态信息的对象 如果promise成功了 对象会有statues为FULFIELD和value的属性 包含成功的值 如果promise失败了 对象有statues rejected和reason的值 包含失败的原因好 我们来看一个promise点oracle的示例 我们首先有一个成功的promise promise点resolve1 以及一个会失败后延迟后失败的promise2 我们把他们啊传入数组 并且传给这个奥赛to o settle 就会等待这个呃两个promise都完成之后 才执行点DAN的回调 我们遍历结果数组去打印每个结果的状态啊 然后就会显示啊这个fulfilled和rejected 可以看到 即使promise2失败了 我们依然拿到了他关于结果的信息 并没有因为失败而中断整个流程 这就使得ASSETTO非常适合执行一组相互独立啊 但是你需要知道所有任务结最终结果了 一个场景 接着看promise点race race顾名思义就是一个竞速 他不像all或者all setto 那样关心所有promise的最终命运 他只等待第一个改变状态的promise Promise 点raise返回的那个额 返回的那个promise的状态啊 以及它的结果与与第一个改变状态 跑得最快的promise完全一致 来看一个示例呃 我们有两个promise promise1会在500ms后解决值是one 然后promise2会在100ms后取resolve值是to 我们将它传给这个promise点rates啊 因为promise2它的延迟更短 它就会先改变状态 所以啊promise点race返回的promise 就会是以promise2的状态和值来解决 来resolve打印出来的结果就是to啊 即使这个promise1稍后也会resolve 他的结果已经被忽略了 race就是看谁先跑完 那么最后是promise点 Any any 就意味着任何一个他专注于在输入的promise中 找到第一个成功解决 也就是full field的promise 对于那些失败就是reject的promise呢 只要还有其他promise没有完成 且有可能成功 安妮就会直接忽略这些失败 如果输入的promise数组中至少有一个 最终呃成功解决 那么promise就会呃点any 返回的promise就会变成resolve 它的值就是那个第一个成功解决的promise值 只有在一种情况下 promise点any 他返回的promise会变成rejected 那就是啊所所有promise都最终失败 此时呢他不会简单地抛出最后一个失败的原因 而是会抛出一个特殊字符串类型 特殊的错误类型叫做aggregate error 这个aggregate error就是一个聚合错误对象 它包含一个errors属性 它是一个数组 收集了所有输入promise拒绝的原因 我们来看any成功的例子 这个呃这里有promise1举例 他是一个立即失败 Promise rejected0 然后promise2延迟100ms去执行成功呃 promise3会延迟500ms传入这个promise 点any啊 把这三个传到这里面 然后promise1失败了 安妮去忽略他 promise2在100ms后成功 这是第一个成功的promise 于是呢promise点any返回的promise 以promise点二的值quick来去resolve 并且通过点代去打印出来 所以他的结果就是quick 再看所有失败的例子 promise4和promise5都是立即失败的 那么传给promise点any呢 因为他们发现所有输入的promise都失败了 它返回的promise就会变成rejected的状态 并且被catch捕获到 打印出来的错误是一个聚合错误实例 通过这个error e r r点errors属性 我们就可以访问到一个数组 里面包含了promise啊的拒绝原因 这里就是一个ERROA和ERROB 那么在使用这些方法时 还有一些需要留意的地方 首先我们前面提到的 如果输入的迭代对象包含非promise的值 他们会被promise点resolve 立即包装成一个已解决的promise来处理 再次强调promise order的FAFFAST的特性 只有只要有一个失败 整体立即失败 不再关心其他额的一个额结果 不太关心其他一个结果 这在某些场景下是很高效的 比如需要所有依赖都成功 才能继续初始化的一个流程 promise点all settled提供了更完整的视角 他总会等到所有的promise都尘埃落定 无论是成功还是失败 并且给你一个包含所有结果列表 详情的一个列表 这就使得它非常适合执行一组独立的任务 即使啊部分任务失败 你也需要知道每个任务的最终状态和结果 promise点any 它的重点是在于找到第一个可用的成功结果 只有当所有的尝试都失败时 他才会进入拒绝状态 并且通过这个聚合错误类型 告诉你失败的原因清单 这种模式就适合你从多个可能的来源 比如多个CDN地址去获取资源 只要有一个成功就行 最后是promise点race 他的一个竞速 他只关心第一个谁第一个改变状态啊 所以所以这就让它非常适合用来实现超时控制 你可以让一个promise和一个一定啊 会一定时间后啊 rejected the promise去竞速 一旦代表超时的promise就先拒绝了 你就知道这个目标任务超时了 所以简单总结一下啊 all就是所有成功才成功 一个失败就失败 all settle是围观 到底只有等待所有的完成 并且给出每个结果的报告 而raise呢是谁到谁谁先到谁说了算 第一个成功或者失败决定最终的结果 而any妮呢是任意一个成功就成功啊 只要有一个成功啊 这个状态就会返回成功 除非所有的事他们都失败了 才会报错 而且是一个聚合错误类型 好希望通过今天的讲解能够帮助大家更深刻 更清晰的理解和区分这四个promise的静态方法 那么在啊我们日常的写代码中 去灵活的运用它啊 感谢大家的观看 我是方格 我们下期再见
