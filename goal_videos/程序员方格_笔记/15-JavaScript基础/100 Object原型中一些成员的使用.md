# 前端面试题笔记：Object 原型中一些成员的使用

## 目录
- Object 原型概述
- `__proto__` 属性
- `toString()` 方法
- `valueOf()` 方法
- `hasOwnProperty()` 方法
- `isPrototypeOf()` 方法及避坑指南
- AI 总结

## Object 原型概述 *Content-[00:01]
- **原型链的顶层**：在 JavaScript 的原型链机制中，所有原型链向上追溯的最顶层就是 `Object.prototype`。
- **全局可用性**：通过 `Object.prototype` 可以查看其内部包含了大量的属性和方法。因为所有对象的原型链最终都指向 `Object.prototype`，所以该原型上的属性和方法是**所有对象都可以调用**的，它是所有对象的“祖宗”。
- 本节主要学习 `Object.prototype` 中一些常用的属性和方法的具体使用。

## `__proto__` 属性 *Content-[01:19]
- **基本用法**：`Object.prototype.__proto__`。
- **核心作用**：用于对象访问，获取当前对象对应的原型对象（即隐式原型）。通过对象查找原型的机制在之前的原型链课程中已经详细讲解过，此处作为 `Object` 原型自带的一个基础成员进行回顾。

## `toString()` 方法 *Content-[02:30]
- **基本定义**：返回对象的字符串表示形式。
- **不同数据类型的表现**：
  - **数组（Array）**：调用 `toString()` 返回的是数组元素拼接成的字符串。
  - **普通对象（Object）**：调用 `toString()` 返回的是 `[object Object]`（包含类型名和构造函数名）。
- **方法重写（Override）机制**：
  - 为什么数组和普通对象的 `toString()` 返回结果不同？因为宿主环境（如浏览器或 Node.js）对某些内置对象（如 `Array`）的 `toString` 方法进行了**重写**。
  - 宿主环境认为默认的方法功能不够用，因此会在各自的原型链中单独编写一份特有的实现。
  - **查看源码技巧**：在代码编辑器中，可以按住 `Ctrl` 键并将鼠标悬停在方法名上，点击即可查看其底层源码（例如查看 `Array.prototype.toString` 的实现）。

## `valueOf()` 方法 *Content-[04:36]
- **基本定义**：返回对象的原始值，即对象原本是什么样子的，就返回什么样。
- **默认行为**：在日常开发中，当我们使用 `console.log()` 打印一个对象时，底层默认调用的就是 `valueOf()` 方法来获取其原始值进行输出。

## `hasOwnProperty()` 方法 *Content-[05:19]
- **基本定义**：判断属性是否属于当前对象**本身**，并且该属性**非原型链属性**。
- **调用语法**：`对象.hasOwnProperty('属性名')`，返回布尔值。
- **示例分析**：
  - 定义构造函数 `Person`，在内部通过 `this.name = name` 和 `this.age = age` 添加实例属性。
  - 在 `Person` 上添加属性 `country = '地球'`（作为原型或静态属性）。
  - 实例化对象 `let p = new Person()`。此时 `p` 可以访问到 `name`、`age` 和 `country` 三个属性。
  - **判断结果**：
    - `p.hasOwnProperty('name')` 返回 `true`（属于自身属性）。
    - `p.hasOwnProperty('age')` 返回 `true`（属于自身属性）。
    - `p.hasOwnProperty('country')` 返回 `false`（虽然能访问到，但它属于原型属性，非自身独有）。
    - `p.hasOwnProperty('不存在的属性')` 返回 `false`。
- **查找机制**：该方法只会在对象自身内部查找，如果自身没有，即使原型链上有该属性，也会返回 `false`。

## `isPrototypeOf()` 方法及避坑指南 *Content-[09:02]
- **基本定义**：判断一个对象是否处在当前对象的原型链中（通俗来说，就是判断对象1是否是对象2的“妈妈、姥姥、太姥姥”等祖宗）。
- **调用语法**：`对象1.isPrototypeOf(对象2)`，返回布尔值，表示对象1是否在对象2的原型链中。
- **常规示例**：
  - 将 `Person` 实例的原型替换为对象 `o`。
  - 调用 `o.isPrototypeOf(p)`，返回 `true`，因为 `o` 确实是 `p` 原型链上的祖宗。
- **⚠️ 避坑指南（重点误区）**：
  - **场景代码**：
    ```javascript
    function Person() {}
    function Animal() {}
    Animal.prototype = new Person(); // 将 Person 的实例作为 Animal 的原型
    let ani = new Animal();
    ```
  - **错误判断**：执行 `new Person().isPrototypeOf(ani)`，结果返回 **`false`**。
  - **原因剖析**：
    - 必须深刻理解 `new` 关键字的作用：每次使用 `new` 都会开辟新的内存空间，创建一个**全新**的对象。
    - 在 `Animal.prototype = new Person()` 时，创建了一个 `Person` 实例（对象A）并赋值给原型。
    - 在后续判断 `new Person().isPrototypeOf(ani)` 时，又创建了一个**全新的** `Person` 实例（对象B）。
    - 对象A和对象B虽然都是 `Person` 的实例（同父兄弟），但它们是两个完全独立的内存实体，没有任何关系。因此，对象B绝对不是对象A（即 `ani` 的原型）的祖宗，结果必然为 `false`。

## AI 总结
本节视频深入讲解了 `Object.prototype` 中几个核心成员的使用方法及底层原理。首先明确了 `Object.prototype` 作为原型链顶层的全局重要性。接着详细拆解了 `__proto__`（获取原型）、`toString()`（转字符串及宿主环境重写机制）、`valueOf()`（获取原始值）的基础用法。重点剖析了 `hasOwnProperty()` 用于区分自身属性与原型属性的判断逻辑，以及 `isPrototypeOf()` 用于校验原型链继承关系的方法。最后，通过一个经典的 `new` 关键字误区，深刻揭示了 JavaScript 中对象引用与内存开辟的本质，帮助开发者在面试和实际开发中避开原型链判断的常见陷阱。

---

## 文稿转写

好各位同学大家好 之前给大家讲过了圆形圆形链对吧好 那么我们也现在知道了 圆形链的最顶层就是object的原型对吧 那么之前我们也打印过来 再给大家打印一下啊 object原型其实里面带了很多东西啊 我们看一下啊 打印object原型就直接输出 object构造函数的妻子 对不对啊 object点prototype 来我们运行一下 这里面带了很多东西啊 带了很多东西 那么大家反应过过来一个问题 我们所有圆形量倒到最上层 也就是一直捋捋到最上层 其实就是object原型 所以我可以认为这里面的无论是属性和方法 是所有对象可以调用的啊 所有对象可以调用的啊 这么理解是没有错的 因为所有的原型原型量 这最顶层都是object原型 所以也就是说他是所有对象的组中 那就所有对象可以调用 所以今天我们要学习的就是 这里面一些常用的属性啊和方法干嘛的 首先第一个杠杠pro to杠杠来写上 object原型里面的一些成一些成员 好第一个我们的什么呢 object点prototype 点杠杠 PROTO杠杠 啊来我们看我们能用的啊我们能用的 啊这CURROUTER以后 后面我们再去说好了 这个对象访问 获取当前对象对应的原型对象对吧 哎对象访问的通过对象找原型的之前就讲过 所以不再展开了啊 不再展开了好 接下来我们看TOSTRING 返回对象的什么字符串表示形式 啊返回对象的字符串表示形式 什么意思啊 light个AR等于中框 我们打一下AR点TOSTR 看看所谓的字符串表形式 就这样 在数组当中 字符串表示表示形式也就TOSTRING 它返回的是这样好 再来个对象light一个P等于大括 那张三就张三吧 把那些省事 好然后我们打印 打印什么呢 P点什么 Tostring 就这玩意 所以普通对象的TOSTRING返回的是什么 第一个它的类型名type p名 第二个它的构造函数名 然后中括号对吧啊 所以普通对象打印的是这个 那就证明什么呢 宿主有把这个方法叫改写过 也就是说怎么样呢 什么叫改写过呢 就是他自己特有的啊 他自己特有的 你看这上面写的arread to4句 你看注意上面这是object to句 看到了吧 这怎么出来的 我按住CTRL啊 CTRL键 然后呢鼠标放上去就行了 这上面是ARREADARREAD 什么突局方法 也就是说什么意思 国家给分配一套方法 我看不上 或者说我觉得功能不够用 我什么样 我自己单独改一份啊 自己在自己的原型量里面再单独写一份啊 是这样的 所以这就是TOSTRING好 那value of呢 value返回的是对象原始值 所谓的对象原始值就是对象原本是什么样子的 就返回什么样 比如AR点value of 然后同时打印 P点value of 看一下效果 大家发现平时我们打印宿主 打印对象是不是默认打印就是value对 就是这样的 平时我们在调用to那个console log打印对象时 它调用的就是value of 原始值啊好 那么我们重点说一下下面这两个 is has own property判断 属性是否属于当前对象 并且该属性非圆形属性 啥意思 来function person Name age this点name等于name this点H等于H好 当然不在这里写函数了啊 不在写函数了 然后呢写上person点 点c o u NC o u n t r y country等于地球是吧啊 等于地球好了 现在我light一个什么呢 P等于new person 现在请问P能够访问到的属性有几个对吧 P能访问到属性有几个 三个P点name p点age以及P点country点name点age啊 这个说白了我们一直在用啊 所以我就不再调用了这个P点country 我们看能不能访问到可以没问题 但是他在圆形当中吧 所以现在我们调用这方法叫对象点 Has own property of 对象点has own property of 属性名是这样调用的 来我们打印 P点has own n property property of has own property啊 来我们看一下has own property 然后呢写上属性名 比如说写上name age 再写一个COUNTRY 再写个不存在的 来分别看下效果 has own property写错了吗 看一下property object has own property啊 是不是什么呀 来 Has on property 对吧啊 P怎么样没有大写啊 好来我们调用一下true true false false来 首先这是当前对象本身的属性 没有问题没有问题 然后注意country虽然这个属性也能调用到 但是它是不是属于原型属性 对不对 所以说呢不属于它自己本身的 属于原型里面的不行 首先呵呵 那么呵呵 首先它会在对象里面找有没有合和属性 没有去原型里面找 没有去原型那里找没有 所以false啊 所以这就是什么呢 Has one property 可以判断一个对象是否拥有指定属性啊 而非原型链属性好判断对象是否是当前对象 是否处在当前对象的原型链中 那么注意看官方的注释啊 Is property A prototype of 返回布尔值 表示指定对象是否处在本对象的原型链中 啥意思 Is prototype of 就是说白了判断一个对象 是否是当前对象的妈妈姥姥 太姥姥 祖姥姥等 就是你上面的祖宗里有没有这对象对象 来看一下 来function person 好我属性不要了 light一个O等于大括号 好现在我把这个原型替换成O 然后我light一个P等于new person 现在我要做的是这样做 O点is pro to type of p 注意是 对象一点prototype of 对象二这样调用的表示 判断对象一是否是否在对象二的原型链中 就是对象一是否是对象二的什么祖宗好了 那么我们现在看现在我判断O是不是P的祖宗 看效果运行是不是没错呀 欧布特特妈妈吗 刚替换的吗 这就是这个属性的使用啊 这就是这个属性的使用 那么当然这个属性 啊这个属性在用的时候 大家一定要规避一个误区啊 一定要规避一个误区 什么误区呢 来 Function person 然后干嘛呢 我再来一个function 然后呢 Animal 然后写上 animal点prototype等于new person 是不是相当于把人的对象作为动物的原型好 接下来我们判断我light个ANI等于new animal 然后呢判断new person 点is prototype of我们的nn i new person 是不是NI的祖宗 思考一下 那么大家看一下这个返回true还是false 来我们看false 不知道有没有没反应过来的同学 可能很反应快的同学现在已经看到了啊 那么注意没反应过来学 看这狠狠记住new关键字的四个作用 第一个开辟内存空间存储新创建的对象新新 这是不是俩新 所以请问这个对象是这个吗 不是他俩不是同一个对象 每new一次就会创建一个新的 所以这是新的 这又是新的 他俩都没有半毛钱关系 他俩唯一的关系就是他们爹都是person神 但是他同父的兄弟不是同一个人 所以他肯定不是他祖宗 这个是 但是你又办法没办法把这个拿过来 为什么 因为这是什么new一次就完事 就给他了吧 对不对啊 就给他了 所以说呢只要注意这是false啊 这是false啊 这就是object1些常用的啊 成员也就属性的方法的使用
