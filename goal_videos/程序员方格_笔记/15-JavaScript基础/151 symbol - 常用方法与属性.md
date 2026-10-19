# 【2026最新】前端面试题：Symbol 常用方法与属性

## 目录
- Symbol.for() 方法
- Symbol.keyFor() 方法
- description 属性
- description 与 Symbol.keyFor() 的区别
- AI 总结

## Symbol.for() 方法 *Content-[00:04]
- **作用**：在全局 Symbol 注册表中创建或者获取 Symbol 的值。
- **特点**：相同描述的 Symbol 值在全局注册表中是唯一的。
- **语法**：`Symbol.for(description)`
- **核心逻辑**：
  - 检测全局注册表中是否存在该描述的 Symbol 值。
  - 如果存在，则返回已有的值。
  - 如果不存在，则新建一个并注册到全局注册表中。
- **代码示例**：
  ```javascript
  const s1 = Symbol.for('描述相同');
  const s2 = Symbol.for('描述相同');
  console.log(s1 === s2); // 输出: true
  ```
- **与 `Symbol()` 的核心区别**：
  - **唯一性**：`Symbol()` 始终新建，即使描述相同也不相等；`Symbol.for()` 在全局注册表中唯一，描述相同则相等。
  - **全局注册表**：`Symbol()` 不会向全局注册表注册；`Symbol.for()` 会注册到全局注册表中。
  - **适用场景**：`Symbol()` 适用于局部唯一；`Symbol.for()` 适用于全局唯一，如跨文件或跨作用域的场景。

## Symbol.keyFor() 方法 *Content-[02:20]
- **作用**：从全局 Symbol 注册表中获取指定 Symbol 值对应的描述字符串。
- **语法**：`Symbol.keyFor(symbolValue)`
- **返回值**：
  - 如果存在，则返回对应的描述字符串。
  - 如果不存在，则返回 `undefined`。
- **限制条件**：仅对通过 `Symbol.for()` 创建的 Symbol 有效。
- **代码示例**：
  ```javascript
  // 使用 Symbol.for() 创建
  const s1 = Symbol.for('test');
  console.log(Symbol.keyFor(s1)); // 输出: 'test'

  // 使用 Symbol() 创建（未注册到全局）
  const s2 = Symbol('test');
  console.log(Symbol.keyFor(s2)); // 输出: undefined
  ```

## description 属性 *Content-[04:45]
- **作用**：获取任意 Symbol 值的描述字符串（ES2019 新增特性）。
- **适用范围**：包括使用 `Symbol()` 和 `Symbol.for()` 创建的所有 Symbol。
- **语法**：`symbolValue.description`
- **返回值**：
  - 有描述则返回描述字符串。
  - 无描述则返回 `undefined`。
- **代码示例**：
  ```javascript
  // 使用 Symbol() 创建
  const s1 = Symbol('test');
  console.log(s1.description); // 输出: 'test'

  // 使用 Symbol.for() 创建
  const s2 = Symbol.for('title');
  console.log(s2.description); // 输出: 'title'

  // 无描述的 Symbol
  const s3 = Symbol();
  console.log(s3.description); // 输出: undefined
  ```

## description 与 Symbol.keyFor() 的区别 *Content-[07:01]
- **适用范围**：
  - `description` 属性：适用于所有的 Symbol 值，无论是 `Symbol()` 还是 `Symbol.for()` 创建的。
  - `Symbol.keyFor()`：仅适用于通过 `Symbol.for()` 创建的 Symbol。
- **查找位置**：
  - `description`：直接获取 Symbol 自身的描述。
  - `Symbol.keyFor()`：从全局 Symbol 注册表中进行查找。
- **返回值**：两者在找到描述时都返回描述字符串，找不到时都返回 `undefined`。

## AI 总结
本次视频详细讲解了 JavaScript 中 `Symbol` 的常用方法与属性，重点对比了 `Symbol()` 与 `Symbol.for()` 的核心区别。`Symbol.for()` 通过全局注册表实现了跨作用域的全局唯一性，而 `Symbol()` 仅保证局部唯一。同时，介绍了如何获取 Symbol 的描述：`Symbol.keyFor()` 专门用于从全局注册表中反查 `Symbol.for()` 创建的 Symbol 描述，而 ES2019 新增的 `description` 属性则提供了一种通用的方式，可以直接获取任何 Symbol 实例的描述字符串。掌握这些细节对于应对前端大厂面试中的 Symbol 考点至关重要。

---

## 文稿转写

再来看常用的方法与属性 symbol点form方法 它的作用就是在全局symbol注册表中 创建或者是获取symbol的值 相同描述的symbol值在全局注册表中唯一 它的语法就是symbol点for 后面加上description scription 描述核心逻辑 就是检测全局注册表中是否存在 该描述的symbol值 存在则返回已有值 不存在则新建并注册到全局注册表中 我们来写个例子给大家感受一下哈 S1等于symbol for注描述相同 S 2symbol for 好如果描述相同 它俩就是相等的保存 它的结果就是true 看到了吗啊 相同描述 它们的两者是相等的 那我们来看一下它与symbol的核心区别 特点特性唯一性 symbol呢是始终信建描述相同也不相等 而symbol for呢全局注册表中唯一描述相同 则相等 全局注册表symbol呢它不往全局注册表注册 不注册 而symbol for呢是注册到全局注册表 适用场景局部唯一 symbol for是全局唯一跨文件或者是跨作用域 你用simple for好吧 那现在呢我就要问一下大家了啊 大家呢在弹幕上走一波 看看大家有没有好好听 那么symbol和symbol for for的核心区别是什么 两者核心区别你觉得是什么 symbol始终新建 而SY不注册 而symbol for呢是全局注册表V1 他要注册好吗 注意啊 你记住这个 symbol呢它是始终新建不注册 而symbol呢它是a symbol for呢 它是全局注册表中唯一它是要注册的 好总结一下好吧 那我们再来看symbol key for 它的作用呢就是什么 从全局波注册表中获取指定的simple值 对应的描述字符串语法 Symbol key for 然后symbol value返回值存在则返回描述字符串 不存在则返回undefined 仅对symbol for创建的有效 好吧 我们来写一下 给大家一个例子 在这里呃 咱用symbol for创建了一个描述为test 对不对 那咱看一下啊 console点log symbol 点key for 对不对 key for f大写 然后输入咱的S1返回 如果存在它就返回test 对不对 这个不要了 如果不存在 那就是啊你反存在吗 存在存在就返回描述嘛 这不就是test嘛 对不对 还有我们再来一个啊 这个是用symbol for for symbol 点for创建的 能获取到描述 然后我们再来一个用symbol创建的 你试试 创建的未注册 返回undefined simple form 创建的是注册的啊 注册了 能获取到描述 我们来试一个 来一个S2等于SYMBO 来一个test 这时候你用symbol key for 它是取不到的 SYMBO点key for 然后来S2保存 那就是undefined 哦这里已经有了 咱给他干掉 好刷新欧米饭 对不对 那我们再来看它的哎 把这个例子给大家放到这里哈 好嘞 我们再来看它的属性 Description 它的作用获取任意symbol值的描述字符串 包括symbol创建的或symbol for创建的 这个是2019新增的 它的语法呢就是symbol value 点description返回值 有描述则返回描述字符串 无描述则返回undefined 我们来看第一个sable创建的能获取simple放 创建的也能获取无描述的symbol 返回UNDEFINDER 我们先来看SYL创建的啊 CONST的S1等于一个symbol标识 就叫test 然后接下来我们来获取一下S1点DISCRIPTION 对不对 可ray Scription this corruption 对吧 好刷新没问题吧 就取到了标识那个标识符了嘛 然后我们再来看这是用SYL创建的啊 再来看用simple form创建的 S2等于symbol点for 换一个吧 叫做title S2点第4SCRIPTION 那就返回title呗 那我们再来一个五秒数的 S3等于symbol 没有描述 没有描述 那就返回undefined description on the f 对吧 好 把这些我们放到笔记上 好那我们再来看description与key for的区别 description这个属性呢它的适用范围 所有的symbol值 不管你是用SYL创建的 还是symbol for创建的都可以 而这个key for呢 它只能是用symbol for创建的查找位置 description呢是自身的描述 而这个for key呢 key for呢它呢是全局symbol注册表的值返回值 描述符 描述字符串或者是undefined 而key for呢也是一样的 描述字符串或者是undefined也都可以
