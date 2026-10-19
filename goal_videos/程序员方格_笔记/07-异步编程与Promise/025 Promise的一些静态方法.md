# 【前端面试题】Promise 静态方法详解 (all, race, any, resolve, reject)

## 目录
- Promise.all 详解
- Promise.race 详解
- Promise.any 详解
- Promise.resolve 与 Promise.reject 详解
- AI 总结

## Promise.all 详解 *Content-[00:57]

`Promise.all` 用于将多个 Promise 实例包装成一个新的 Promise 实例。

### 基本用法与代码示例
- **参数**：接收一个数组，数组中放置多个 Promise 实例。
- **返回值**：返回一个新的 Promise 对象。

**代码逻辑还原**：
封装一个异步计算相加的方法 `sum(a, b, timeout)`：
- 传入两个数字 `a` 和 `b`，以及计算延迟时间 `timeout`。
- 内部使用 `setTimeout` 模拟异步操作。
- 如果参数类型正确（均为 number），则 `resolve(a + b)`；否则 `reject('参数错误')`。

```javascript
function sum(a, b, timeout) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      if (typeof a === 'number' && typeof b === 'number') {
        resolve(a + b);
      } else {
        reject('参数错误');
      }
    }, timeout);
  });
}

const p1 = sum(1, 2, 1000); // 1秒后返回 3
const p2 = sum(3, 4, 3000); // 3秒后返回 7
const p3 = sum(5, 6, 2000); // 2秒后返回 11

const p = Promise.all([p1, p2, p3]);
p.then(data => console.log(data));
```

### 执行逻辑与状态变化
1. **等待所有完成**：`Promise.all` 会等待参数内**所有** Promise 异步代码执行完毕，才会触发 `then` 或 `catch`。
2. **结果数组排序**：`then` 接收到的结果是一个数组，包含所有 Promise 的成功结果。
   - *专业纠正*：结果数组**严格按照传入参数的顺序排列**（即 `[p1结果, p2结果, p3结果]` = `[3, 7, 11]`）。（注：视频中讲师口误称“按执行完毕的先后顺序排列”，实际 ES6 规范为按传入顺序排列）。
3. **短路机制（失败处理）**：
   - 如果其中**任何一个** Promise 状态变成 `rejected`，整体的状态就会立刻变成 `rejected`。
   - 直接触发 `catch`，**不再等待其他 Promise 的结果**。（注：底层异步操作如 setTimeout 仍会执行，但 `Promise.all` 不再收集和处理它们的返回值）。
   - 只有当所有 Promise 都 `fulfilled` 时，才会统一将结果放入数组并触发 `then`。

## Promise.race 详解 *Content-[07:27]

`Promise.race` 的“race”英文意为赛跑、竞赛。它的核心机制是“谁先出结果，就听谁的”。

### 基本用法
- **参数**：与 `Promise.all` 一样，传入包含多个 Promise 的数组。
- **返回值**：返回一个新的 Promise 对象。

### 执行逻辑
- **比赛机制**：哪个 Promise 对象**最先执行完毕**（无论成功还是失败），就会按照该先出结果的状态作为 `Promise.race` 本身的状态。
- **状态决定**：完全取决于第一个执行完的 Promise 是 `fulfilled` 还是 `rejected`。
  - 如果第一个完成的是成功，则 `race` 返回 `fulfilled`。
  - 如果第一个完成的是失败，则 `race` 返回 `rejected`。

### 实际应用场景
- 实际开发中相对使用较少，主要用于一些特定的并发控制场景（例如：为网络请求设置超时控制，将一个业务请求与一个超时 Promise 进行 race）。

## Promise.any 详解 *Content-[10:19]

`Promise.any` 接收一组 Promise 实例，其核心逻辑类似于逻辑或（`||`），口诀为：**全假才假，一真即真**。

### 执行逻辑与状态变化
1. **一真即真**：只要参数实例中**有一个**变成 `fulfilled`，包装后的 Promise 就会立刻变成 `fulfilled`，并以该成功的结果作为返回值。不会等待其他执行较慢的 Promise。
2. **全假才假**：只有当**所有**传入的 Promise 都变成 `rejected` 时，包装后的 Promise 才会变成 `rejected`（此时会抛出一个 `AggregateError`，提示 `All promises were rejected`）。

### 代码示例分析
- 假设传入多个 Promise，有的 1 秒成功，有的 2 秒失败，有的 4 秒成功。
- 如果 1 秒的 Promise 成功了，`Promise.any` 会立刻返回成功结果，直接结束，不会等待后面 2 秒或 4 秒的 Promise。
- 如果前面的 Promise 都是失败的（rejected），它会一直等待，直到遇到第一个成功的（比如 4 秒的那个），然后以该成功的结果返回。
- 如果把所有成功的 Promise 都去掉，全部换成失败的，那么它会一直等到所有 Promise 都执行完毕，最后返回 `rejected`。

### 与 Promise.race 的区别
- `Promise.race`：比的是**速度**，谁先完成听谁的（不管成功还是失败）。
- `Promise.any`：比的是**成功**，谁先成功听谁的（必须成功，全失败才失败）。

## Promise.resolve 与 Promise.reject 详解 *Content-[14:41]

这两个方法用于快速创建一个特定状态的 Promise 实例。

- **Promise.reject**：
  - 返回一个新的 Promise 实例。
  - 该实例的状态直接为 `rejected`。
  - 相当于直接返回一个失败状态，常用于快速抛出错误。

- **Promise.resolve**：
  - 返回一个新的 Promise 实例。
  - 该实例的状态直接为 `fulfilled`。
  - 相当于直接返回一个成功状态，常用于将同步值快速包装为 Promise 对象以保持 API 的一致性。

## AI 总结

本视频详细讲解了前端面试和实际开发中常用的 `Promise` 静态方法：
1. **`Promise.all`**：适用于需要**并行执行**多个异步任务，且**必须全部成功**才继续后续操作的场景。具有“一假即假”的短路特性。
2. **`Promise.race`**：适用于**竞速场景**，以第一个完成（无论成败）的 Promise 结果为准。
3. **`Promise.any`**：适用于**容错与竞速结合**的场景，只要有一个成功即可，具有“一真即真，全假才假”的特性。
4. **`Promise.resolve / reject`**：用于快速构造已成功或已失败的 Promise 实例。

掌握这些静态方法的状态流转规则（特别是 `all` 的短路机制和 `any` 的聚合错误），是应对前端大厂面试中 Promise 深度考察的关键。

---

## 文稿转写

好那么接下来我们再看promise 其实还有三个静态方法 有的时候面试也会问 实际开发也偶尔也会用到叫promise all promise rise以及promise any 什么意思啊 甚至还有两个叫promise resolve和promise reject 我们先看前三个 promise的一些静态方法 叫promise点rise 然后promise点all promise点any 然后呢promise点resolve和promise点reject 我们先看前三个 来一个一个看 先看第一个叫promise all Promise all 用于将多个promise力包装成一个新的promise力 什么意思 也就是说它里边传数组 数组里面放多个promise来 我们封装一个方法 Function sub A和B逗号time out 什么意思 我想封装一个呀 就是你自己给传入计算时间啊 异步计算时间的一个方法 然后return new promise 然后里边resolve reject 还是我们的计算 然后set time out 然后呢就用它的time out 你传time out 然后呢判断if如果type of a等等number 并且这个 就reject参数错误 然后就resolve a加B能看懂代码吧 啊也就是说什么意思呢 你给我传入一个两个数字 我给你计算相加 然后你给我传入计算相加时间好了 那现在我要做的事情来了 light一个P1等于SU12用一秒时间 然后再来P2P3 然后3+4用的时间最长三秒 然后呢5+6 用的时间中等两秒 然后呢我们去看一下啊 我们去看一下promise race 它的返回值 啊promise race Promise all 我们先看all 它返回的也是一个promise对象 啊它返回的也是promise对象 什么意思呢 宿主多个promise对象 啊这里传多个promise对象 然后返回什么呢 返回一个promise对象 那这返回对象有啥用呢 来看效果light一个 P等于promise点all 然后传数组里边写上P1逗号P2 把这两个传进去 P3 然后这个promise对象P点D 我们接收一下 看什么情况 直接打印data 刷新 大家会发现嗯 时间等的很长 对不对 不是一秒 不是两秒 也不是三秒 那是多少秒呢 我大概猜是六秒 为啥呢 一会我们说 然后呢 大家再注意看他的计算结果出来了 1+23加45+6对吧 所以在这里写上他是干嘛返回promise对象 然后说等到只有等到什么呢 all方法参数内的所有promise异步代码执行完毕 返回值的promise对象 触发done或者catch 然后呢 then里面接收到的结果是一个是一个数组 什么呢 数组里面包含所有promise的结果 按照什么呢 执行的 执行完毕的先后顺序排列 注意P1先执行完P3 第二执行完P2 最后一个执行完 所以他的结果是P1P3P二 所以是三七十一这么放的 所以all是相当于把多个promise统一执行 然后等到所有执行完毕再去输出结果 当然这里面我就不再过多的绕了 那么老师如果中间有个promise 他的状态不对 他是catch呢 那么结果就是catch 如果如果其中有一个promise 状态变成了rejected 那么整体的状态就是rejected 然后呢执行catch 结果当然这个呃我就用嘴说了啊 要说起他写写字多大 蒙什么意思呢 他什么时候触发catch呢 也就是说什么意思啊 它虽然说是执行内部所有的promise 但是一旦有其中一个就执行的过程当中 比如说啊执行两秒 这个他错了 那么就整个程序就停了 不再执行P4P2了 就后面不再执行了 也就是说直接就catch了 就是按怎么呢 统一执行所有promise 但凡有其中一个坏了这一锅汤他失败了 那么直接跳到失败 其他未执行的就不再执行了 就这意思只有所有的都正确了 都匹配done了 那么就相当于所有等等都执行完 最后一股脑放进去 这是promise all 讲完了啊 就这么用啊 就这么用好 那接下来看promise点race 来看一下prompter race 它也传一个数组 同样传多个promise li来light一个P等于promise点 Rise 参数也传宿主P1P2P三好 然后呢用它匹配P点正 我们打印done的结果 看一下 嗯完事了 不用等了没了 race什么意思呢 跟or使用方式一样 唯一区别是race是进行比赛 哪个promise对象先出结果 就会按照先出的结果为raise本身的结果 所以raise有可能是什么呢 Full field 这么写吧 看一下fulfilled是这么写吗 哦前面读起来有fulfilled 也有可能可能是rejected 然后呢 完全取决于第一个执行完的promise是什么状态 所以rise是一种比赛的意思啊 rise这个单词来我们查一下它的英文中的意思 翻译点百度点com来 你弹出来我能看你是咋的 真的是瞎弹 赛跑看到了吗 赛跑竞赛的意思 所以他本身就是比赛 瑞士讲完了 你也不要问我说老师这玩意实际有什么用 你记住它这个功能就行了 我我没没必要说为了给你理解他实际怎么用 我给你讲个项目吧 这玩意没有什么小案例能用它啊 这我举的这就是这就是例子了啊 这就是案例了啊 不要问我啊 我也不知道他这这这这这能怎么能 什么例子能用它就证明什么 实际开发用的相对来说比较少啊 相对来说比较少 好any来看promise all用的还可以 raise和any几乎不是很少用 接收一组 只要参数实例有一个变成付费 有的包装就会变成负费 有的如果所有都变成rejected 那么包装注意它跟rise还不一样 瑞士是以谁执行快为结果 它是什么呢 所有的就是相当于什么全真为真 啊什么呢 注意看啊 来重新分析一下参数 实例只有一个 有一个变成这个包装 就会变成这个就是全假为假 一真即真是有货的关系 看到了吗 全假才假 一真即真 我们现在再来一个来个P47和一个假的BB 一好假的 然后它呢两秒promise any Upromise in it 来注意看啊 注意看现在P点D 看什么结果 打印data 先看结果 回头慢慢分析 过一秒后执行结束了 注意P4 我传进去了啊 轮到他了吗 没有一上来P1就一秒执行完嗯 真的好 直接真了 所以any跟raise 用法使用方式 一样 但是any作用是 全re reject 全rejected才rejected 只要有一个FULFIELD 则any 结果就是夫field口诀 全假才假 一真即真 只要有一个是真的 那么就是真的 所以也就是说它是都是直行的 只不过是看到有一个真的了 那么他直接就怎么样了 就真了 来再来一个P5P6 然后怎么样呢 两秒三秒四秒 然后789注意 然后呢我找个时间最长的四 把它改成五秒 P2P4呃P4P5P六 我用这个来P2P4P5P6 P 2p4 p 5p6 那么大家注意P2时间是最长的 这些假的咱看能不能轮到 也就是说能不能等到P2执行来看一下 大家注意看是不是等到了P2 P2等于七吗 是不是等到了P2这些其实他也尝试执行了 但是怎么样呢 不好意思 它都是假的 所以我一定要等到真的那个出现 那么等到最后也没有真的才是假的 也就说一看诶 最后A真有一个真的 那么以真的为结果 那如果把P2拿掉 嗯最后结果就就all promise were什么reacted 所有promise都是假的啊 就全假才假啊 这就是any好 完事了啊完事了啊 那么这是什么呢啊这是我们的这三个静态方法 当然还有这个promise reject方法会返回新的promise里 该实际状态为reject 相当于直接返回rejected 啊这个我就不再讲了 直接告诉大家就行了 相当于他直接直接返回一个rejected 然后同样的promise solve resolve 直接返回一个pro状态为FULFIELD的啊 这么一个东西 这个等到遇聚到具体例 遇到具体例子 我去给大家详细去分析好 promise我们就讲完了
