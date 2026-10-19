# 前端面试：null 和 undefined 的区别（差异篇）

## 目录
- 数据类型差异 *Content-[00:00]
- 数值转换差异 *Content-[02:59]
- 严格相等比较 *Content-[05:18]
- AI 总结

## 数据类型差异 *Content-[00:00]
- **`undefined` 类型**：
  - 属于 `undefined` 类型，该类型只有一个值，即 `undefined`。
  - 使用 `typeof` 检测时，`typeof undefined` 返回 `"undefined"`，可以精准判断。
- **`null` 类型**：
  - 属于 `Null` 类型，该类型也只有一个值，即 `null`。
  - 使用 `typeof` 检测时，`typeof null` 返回 `"object"`，而不是 `"null"`。
- **`typeof null === "object"` 的历史 Bug 解析**：
  - 这是 JavaScript 的历史遗留 Bug，主要原因有两点：
    1. **底层存储原因**：JS 存储变量时使用二进制，前三位表示类型标签，`000` 表示对象。而 `null` 的二进制表示全为 `0`，其前三个比特位自然也是 `0`，因此 `typeof` 会将其误判为 `object`。
    2. **逻辑角度原因**：`null` 表示空的对象指针，本意是指向一个不存在的对象。因此从逻辑上来讲，`typeof` 返回 `object` 也能勉强理解。
- **获取真实类型的方法**：
  - 若要获取 `null` 和 `undefined` 的真实类型，需要使用 `Object.prototype.toString.call()` 方法。
  - 示例：`Object.prototype.toString.call(null)` 和 `Object.prototype.toString.call(undefined)`。
  - 该方法可以精准检测所有 JS 内置的数据类型。

## 数值转换差异 *Content-[02:59]
- 在 JS 进行算术运算时，两者的隐式和显式数值转换结果完全不同，这是开发中避免算术 Bug 的关键。
- **`null` 的数值转换**：
  - 转为数值结果是 `0`。因为 `null` 表示空对象，空对象在数学上被视为 `0`。
- **`undefined` 的数值转换**：
  - 转为数值结果是 `NaN`（Not a Number）。表示它不是一个数字，无法参与正常的算术运算。
- **代码验证与示例**：
  - **隐式转换（算术运算）**：
    - `7 + null`：`null` 隐式转为 `0`，最终结果为 `7`。
    - `7 + undefined`：`undefined` 隐式转为 `NaN`，任何数字与 `NaN` 相加结果依然是 `NaN`。
  - **显式转换（使用 `Number()` 方法）**：
    - `Number(null)` 结果为 `0`。
    - `Number(undefined)` 结果为 `NaN`。

## 严格相等比较 *Content-[05:18]
- 使用严格相等运算符 `===` 进行比较时，`null === undefined` 返回 `false`。
- **原理解析**：
  - `===` 是严格相等比较，不会进行任何隐式类型转换。
  - 它要求两边的**数据类型**和**值**都完全相等才会返回 `true`。
  - 由于 `null` 和 `undefined` 的数据类型不同，因此严格比较必然返回 `false`。
- **代码验证**：
  - `null === undefined` 返回 `false`。
  - `null !== undefined` 返回 `true`。

## AI 总结
本视频详细讲解了前端面试中高频考点 `null` 和 `undefined` 的核心差异，主要从三个维度进行剖析：
1. **数据类型**：`typeof undefined` 返回 `"undefined"`，而 `typeof null` 返回 `"object"`，这是由 JS 底层二进制存储和历史遗留问题导致的 Bug，可通过 `Object.prototype.toString.call()` 获取真实类型。
2. **数值转换**：在算术运算或显式转换中，`null` 会被转换为 `0`，而 `undefined` 会被转换为 `NaN`，两者在参与数学计算时表现截然不同。
3. **严格比较**：由于两者类型不同，在使用 `===` 进行严格相等比较时，`null === undefined` 始终返回 `false`。
掌握这些差异有助于在前端开发中避免潜在的类型转换 Bug，并在面试中展现出扎实的 JavaScript 基础。

---

## 文稿转写

再来看差异性 这个差异性呢是面试中的重中指重 从数据类型 数值转换运算符 严格比较三个核心维度给大家 讲解啊 配合代码验证 让零基础的同学也能听听得懂哈 我们首先来看数据类型的不同 undefined呢属于undefined 类型该类型只有一个值 就是on defend 你用type of去检测的话 type of去检测undefined返回的就是undefined 对吧 可以精准判断 那么钠呢它呢属于属于 钠类型 该类型也只有一个值 就是none对吧 如果你用type of 检测钠的类型会返回大家 弹幕上走一波会返回什么 会返回object 它并不是none哈 扣了none的同学注意一下哈 这是一个历史bug 对吧啊 非真实的类型 那真实的类型是什么 是基本数据类型 对不对 哎这里说了啊 这是JS的历史遗留bug 而且前面的视频我们也给大家讲过 原因有两个 第一个呢底层的存储 JS存储变量是用二进制前三位表示类型 标签三个零表示对象 而钠的二进制表示全为零 前三个当然也是零 因此type2误判为object 逻辑的角度呢 N呢表示空的对象 指针本意是指向一个不存在的对象 因此从逻辑上来讲 type of返回object也能勉强理解啊 我们来看一下 用代码给大家演示一下 首先我们来看类型的判断 type of n和on type of n和undefined undefined返回的是undefined 而N呢返回的是object 再来看 如果你要想获取那和undefined真实类型 你得使用什么呀 Object prototype tostring 点coon defined和N 这样的话呢 就能获取undefined和N的真实类型的 当然了 你通过object prototype tostring这个方法的话呢 你可以精准的检测所有JS内置的类型 好其他的视频我们有讲过啊 好那么接下来的话呢我们再来往下看 第二个区别转为数值的结果不同 JS在进行算术 算数运算时两者的数值转换结果完全不同 这是开发中避免算数的算数bug的关键 N转为数值是零啊 表示那本来就表示空对象 对不对 空空对象数学上视为零 而undefined转为数值 十为NAN不是一个数字 对不对啊 表示不是一个数字啊 无法参与算数运算 我们来看一下 把这些代码给大家拿过来执行一个好 首先我们在先来看上面的哈 这个我们先注释掉啊 七加钠 我们知道钠呢会转为零 所以呢最终结果还是七 而undefined呢它呢转为数学 它呢是一个NAN不是一个数字 那么不是一个数字和数字相加是什么 不知道啊 不不知道是个什么东西 所以呢依旧告诉你 不是一个数字 看到了吗 啊 不是一个数字 上面的是七 那我们再来看 把这个给除掉 再把下面的给放开 我们通过显示的方式去转换 上面都是隐式类型转换 我们用显示的number直接转 把那通过number1转就是零 把undefined通过number方法一转 它就是NAN啊 注意转换数值的结果它是不同的啊 那么在这里好 我再问一下七加 那结果是什么 大家弹幕上走一波七加那的结果是什么 哎是什么呀 是不是七呀 那七加undefined呢是什么呀 是不是NAN呐 一定要知道哈 要记清楚 我们再来看第三个 严格相等 严格相等就是三等比较返回false啊 三等我们知道是严格 相等 不会进行任何的类型影视转换对吧 要求类型 和值都完全相等 才会返回丑钠和undefined的数据类型不同 因此严格比较必然返回force对吧 这一段代码跑一下吧 给大家 好保存钠和undefined严格相等 它会返回一个false 然后他俩不相等 严格不相等 它会返回一个true 对不对 证明了他俩呢严格比较返回的是false 我们再来看第四个
