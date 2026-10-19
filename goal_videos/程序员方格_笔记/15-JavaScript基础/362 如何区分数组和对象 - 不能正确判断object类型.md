## 目录
- [instanceof 无法正确判断 Object 类型](#instanceof-无法正确判断-object-类型)
- [原型链深入剖析：数组、函数与 Object 的关系](#原型链深入剖析数组函数与-object-的关系)
- [instanceof 的局限性总结](#instanceof-的局限性总结)
- [自定义类中的 instanceof 表现](#自定义类中的-instanceof-表现)
- [AI 总结](#ai-总结)

## instanceof 无法正确判断 Object 类型 *Content-[00:00]
- 在判断数据类型时，`instanceof` 不能正确判断 `Object` 类型。
- **示例验证**：定义一个数组 `arr`，`arr instanceof Array` 返回 `true`，同时 `arr instanceof Object` 也返回 `true`。
- **原因分析**：数组和 `Object` 同属于一条原型链。所有原型链的尽头都是 `Object`，数组 `arr` 的原型链尽头也是 `Object`，因此判断结果为 `true`。
- **函数同理**：定义一个函数 `fn`，`fn instanceof Function` 返回 `true`，`fn instanceof Object` 也返回 `true`。因为 `Function` 构造函数的原型对象的 `__proto__` 指向的是 `Object.prototype`，它们在同一条原型链上。

## 原型链深入剖析：数组、函数与 Object 的关系 *Content-[02:25]
- **数组实例、`Array` 构造函数与 `Object` 的关系**：
  - 数组实例对象的 `__proto__` 指向 `Array.prototype`（数组构造函数的原型）。
  - `Array.prototype` 的 `__proto__` 指向 `Object.prototype`。
  - `Object.prototype` 的 `__proto__` 指向 `null`，标志着原型链的结束。
  - **结论**：数组实例对象、`Array` 构造函数、`Object` 都在同一条原型链上（可理解为三个节点）。就像你是你父亲的后代，自然也是你爷爷的后代，因此 `instanceof` 判断均为 `true`。
- **函数实例、`Function` 构造函数与 `Object` 的关系**：
  - 实例对象通过 `__proto__` 找到构造函数的原型对象。
  - 构造函数的原型对象通过自己的 `__proto__` 找到 `Object.prototype`。
  - `Object.prototype` 的 `__proto__` 为 `null`，结束原型链。
- **其他内置对象**：
  - 诸如 `Date`（时间日期对象）、`RegExp`（正则对象）等，也会形成对应的原型链，原理与数组和函数完全一致。

## instanceof 的局限性总结 *Content-[06:04]
- `instanceof` 操作符只能用来判断两个对象是否属于**实例关系**。
- 它**不能**判断一个对象实例具体属于哪种类型（例如无法区分到底是数组还是普通对象）。
- 因为对于数组和普通对象，`instanceof Object` 返回的结果都是 `true`，所以最终结论是：`instanceof` 无法区分数组和对象。

## 自定义类中的 instanceof 表现 *Content-[08:00]
- 除了 ECMAScript 中的内置类，自定义类也遵循相同的原型链规则。
- **示例**：定义一个父类 `Parent` 和一个子类 `Child`，通过构造函数让 `Child` 继承 `Parent`。创建子类实例对象 `c1`。
- **判断结果**：
  - `c1 instanceof Child` 为 `true`（`Child.prototype` 在 `c1` 的原型链上）。
  - `c1 instanceof Parent` 为 `true`（`Parent.prototype` 也在 `c1` 的原型链上，因为存在继承关系）。
  - `c1 instanceof Object` 为 `true`（所有对象的顶端都是 `Object`）。
- **结论分析**：
  - `c1` 对 `Child`、`Parent`、`Object` 的 `instanceof` 结果都是 `true`，因此无法区分 `c1` 到底是 `Child` 还是 `Parent` 的实例。
  - 但可以确定 `Child` 和 `Parent` 是继承关系。如果 `Child` 没有继承 `Parent`，那么 `c1 instanceof Parent` 就不会是 `true`，因为 `c1` 的原型链上不会存在 `Parent`。

## AI 总结
本次视频深入讲解了前端面试中 `instanceof` 操作符的底层原理及其局限性。核心要点在于：`instanceof` 是通过查找原型链来判断实例关系的，由于所有内置对象（如 `Array`、`Function`、`Date` 等）以及自定义子类的原型链最终都会指向 `Object.prototype`，导致 `instanceof Object` 始终返回 `true`。因此，`instanceof` 只能用于判断对象之间是否存在继承或实例关系，而无法用于精确区分对象的具体数据类型。在实际开发中，若需精确判断数组等类型，建议结合使用 `Array.isArray()` 或 `Object.prototype.toString.call()` 等方法。

---

## 文稿转写

我们再来往下看 Instead of 它呢是不能正确判断object类型的 其实上面我们已经给大家演示演示过了 不知道大家能不能把这个结论给它得出来哈 其实是这个在数组啊 瑞的圆心链上也能找到 object构造函数的PROTO type属性 所以结果也是true 咱们上面的例子其实就已经验证了 也就是这里的额 这里的这个例子啊 Array instead of a a r2 instance of array是true a r r is this of object也是true对吧 那为什么是这样的 因为其实刚才已经说过了 他们是同属于同一条原型链的 可以给大家呢再来画一画 再来强调一遍哈 这里呢是因为所有原型链的尽头都是object 那么你的数组AR2的原型链的尽头 不也是object吗 所以呢你AR2instead of object返回的也是处对吧 因此就造成了这种情况对吧 函数也是一样的 我们可以来你看下面有啊 你定义了个函数 你的函数本身的话呢 他要找的是function 这个构造函数原型是否在FN的圆形点上 当然是在的呀 那么function的构造函数的原型对象的杠杠 PROTO杠杠是不是又找到的是object的prototype呀 所以呢他们也是在同一条原型链上的 因此你的函数instead of object也是为true的 你可以看一下啊 这是毋庸置疑的 因为他们都是在一条链条上的 好你看结果他们是在同一个链条上的对吧 结果呢他就是一个处嘛对吧 它和数组那个意思呢是一样的 那么我们再来为了大家理解清楚 我们来看一下啊 拿那个数组来分析一下 那就是咱的速度实例以及array构造函数 还有object3者之间的一个关系 其实这个关系呢他们就是在这三者呀 就是在一个链条上的 就是圆形链条上吗 啊我们来给大家说一说啊 从instead of能够判断出数组点上杠杠 pronto杠杠 它指向的是什么 你的arraid pronto type 也就是数组的构造函数的原型 而array点上pronto type点上杠杠 pronto杠杠 他又指又指向了谁呀 又指向了object对吧 object对吧 pronto type原型对象 所以最终啊你的object点上 type点上杠杠 pronto杠杠 它又指向谁啊 它指向的是一个N了 已经没了对吧 指向的式 那这已经到了 标志着当你找到那了 就标志着原型链条结束了 其实到了object就已经结束了哈 你找那没有意义 是不是标志着 原型链结束了 因此你的数组实例对象 还有你的array构造函数 以及你的object 它们是在一条 圆形链上的 你可以理解为它就是三个节点嘛对吧 你就拿这个来说吧 它既属于发个CTION这个节点 同样的FON节点上面是不是还有object点 那当然它也属于object这个节点 就像你对吧 你是你父亲的后代 那么同样的你是不是你爷爷的后代 肯定是嘛对吧 所以呢结果就是true啊 下面还有一幅图 这幅图的话 也准确的表示了这一段文字描述的一个含义 给大家往后拖一拖 大家可以看一看哈 你看一个意思 这个附图呢我就给大家简单解释一下哈 实例对象通过影视原型杠杠PROTO杠杠指向 找到了谁 找到了你的构造函数的原型对象 而构造函数的原型对象又有自己的原影视原型 杠杠PROTO杠杠 他又找到了谁 他又找到了object的的原型对象 那么object的原型对象他自己身上也有杠杠 PROTO杠杠 影视原型 他又找到了谁 那就没有了 对不对啊 这就是一整个圆形链 也就给大家解释了 为什么FN函数它呢instance of function返回的true 而fn instance of object也能返回true 原因还有咱们刚才例子当中的这个数组 这里啊它能返回true 它也能返回TRU 就给大家解释清楚了哈 说白了其实就说白了其实就是这样的啊 就是你的数组的实例对象 实例对象直接指向的是arread pronto type 然后呢又间接的 间接的指向了object点pronto time嘛对吧 哎那么以此类推啊 以此类推 像咱们的时间日期对象 New date 还有咱的 比如说正则呀对吧 也会形成一条对应到 原型链 所以呢instead of呢 它只能用来判断两个对象是否属于实力关系 因此instead of只能用来判断两个对象 是否属于实例关系 而不能判断一个对象实例具体属于哪种 哪个类型 到底是数组还是对象 这个它是区分不了的对吧 instead of操作符对于数组和对象 因为它返回的都是true 所以你最终的结论就是 instead of无法区分数组和对象 因为返回的都是处对吧 那么接下来我们再来看以上咱们说的都是什么 ECMA中的内置的类 那么我们自己定义的类也是这样的吗 你可以测一下 比如说在这里它第一个类 比如说这个叫做父类 那下面这个呢咱又定了一个子类 而这里呢通过一种构造函数子类继承了父类 那么这个时候你再来看C1 C1是什么实例对象对吧 C 1instead of child 不肯定没问题对吧 哎这个child的原型prototype 它就是在C1的原型链上的 这是没有问题的对吧 还有呢当然C1instead of parent也是没有问题的 因为parent原型prototype也是在C1的原型链上的 因为他俩是一个继承的关系好 那么还有我们知道我们对象的顶端是谁 Object 也就是说在这里他们四个形成了一个链条 先是C一C1上面有谁有child Child 上面有谁有parent parent上面有谁有咱们对象的老大object 他们四个属于同一个链条 所以你的C1不管是child还是parent还是object 他的结果都是true 我们来给大家执行一下啊 保存刷新 OK它都是一个true啊 在这里给大家简单的写两句结论哈 结果都是true 无法区分C1实例对象到底是child的 还是parent的 还是object 但是我们可以知道child d和parent是继承的关系 这个是可以确定的 如果说你的child没有继承你的parent 那么c e instead of parent 它的结果就不会是除了 因为在C的原型链上没有parent 是这个逻辑吧
