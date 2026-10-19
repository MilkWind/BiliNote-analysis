# 10月丨建议你的【JavaScript】达到这种程度，再去面试前端开发！ p33 32. instanceof 背后的原理

## 目录
- instanceof 的核心作用与语法
- instanceof 的检测过程与底层原理
- 经典实例分析：继承与原型链检测
- 特殊类型检测：原始类型、包装对象与 null/undefined
- 使用 instanceof 的注意事项与“坑”
- 课程总结与回顾
- AI 总结

## 1. instanceof 的核心作用与语法 *Content-[01:21]

- **核心作用**：`instanceof` 运算符的主要作用是检测某个构造函数的 `prototype` 属性是否出现在某个对象的原型链中的任何位置。它的本质是一个用来判断对象和构造函数之间原型链关系的工具。
- **为什么需要它（对比其他类型判断方法）**：
  - **`typeof`**：在判断基本类型时表现很好，但对于复杂类型（如数组、对象字面量等）区分度不够，都会返回 `object`，无法区分变量到底是数组还是普通对象。
  - **`constructor` 属性**：例如 `arr.constructor === Array`，这种方法有时可行，但 `constructor` 属性是可以被人为修改的，不如基于引擎底层原型链的 `instanceof` 可靠。
  - **`instanceof` 的优势**：它恰好弥补了上述不足，专门用来检测对象和构造函数之间基于原型的“血缘关系”。
- **语法说明**：
  - 格式：`object instanceof Constructor`
  - 左侧：要检测的对象。
  - 右侧：要检测的构造函数。
  - 返回值：布尔值。如果是 `true`，表示该对象是构造函数的实例，或者在其深层原型链上能找到与构造函数原型对象匹配的对象；如果是 `false`，则表示没有这种关系。

## 2. instanceof 的检测过程与底层原理 *Content-[04:21]

- **检测过程**：整个检测过程实际上是一个沿着对象原型链进行的循环查找。
  1. 从对象自身的原型开始（即 `object.__proto__`）。
  2. 将当前访问到的原型对象与构造函数的 `prototype` 属性进行严格相等（`===`）比对。
  3. 如果引用严格相等，`instanceof` 立刻返回 `true`，表示找到匹配关系。
  4. 如果不相等，则继续向上查找，访问当前原型的原型（即 `__proto__.__proto__`）。
  5. 此过程持续进行，直到访问到原型链的终点 `null`。
  6. 如果一直找到 `null` 都没有找到严格相等的对象，则返回 `false`，表示它们之间没有通过 `prototype` 建立原型链关系。
- **伪代码模拟**：
  ```javascript
  function myInstanceof(object, constructor) {
      // 获取对象的原型，效果等同于 object.__proto__
      let proto = Object.getPrototypeOf(object); 
      
      while (true) {
          // 如果到达原型链终点，返回 false
          if (proto === null) {
              return false;
          }
          // 如果当前原型与构造函数的 prototype 严格相等，返回 true
          if (proto === constructor.prototype) {
              return true;
          }
          // 更新原型链，指向当前原型的原型，继续查找下一轮
          proto = Object.getPrototypeOf(proto);
      }
  }
  ```
  *(注：真实的 `instanceof` 是 JavaScript 引擎内置实现的，效率比伪代码更高。)*

## 3. 经典实例分析：继承与原型链检测 *Content-[09:25]

- **代码示例**：通过 `Animal` 和 `Dog` 构造函数演示原型链继承。
  ```javascript
  function Animal(name) {
      this.name = name;
  }
  function Dog(name, breed) {
      Animal.call(this, name); // 属性继承
      this.breed = breed;
  }
  // 建立原型链继承关系
  Dog.prototype = Object.create(Animal.prototype);
  // 修复 constructor 指向
  Dog.prototype.constructor = Dog;

  const myDog = new Dog('Rex', 'Labrador');
  ```
- **检测结果分析**：
  - `myDog instanceof Dog`：返回 `true`。`myDog.__proto__` 正好是 `Dog.prototype`，第一次匹配就成功。
  - `myDog instanceof Animal`：返回 `true`。在 `Dog.prototype` 上未找到匹配，继续向上查找到 `Animal.prototype`，匹配成功。印证了 `instanceof` 能够检测整条原型链上的关系。
  - `myDog instanceof Object`：返回 `true`。继续沿着原型链向上，经过 `Dog` 和 `Animal`，最终到达原型链顶点 `Object.prototype`，匹配成功。这反映了所有对象最终都继承自 `Object` 的事实。

## 4. 特殊类型检测：原始类型、包装对象与 null/undefined *Content-[12:41]

- **原始类型 vs 包装对象**：
  - **原始字符串**：`const str = 'hello'; str instanceof String` 返回 `false`。因为原始类型没有原型链，不是通过构造函数创建的对象，试图访问 `str.__proto__` 会得到 `undefined` 或引发错误，自然找不到 `String.prototype`。
  - **包装对象**：`const objStr = new String('hello'); objStr instanceof String` 返回 `true`。因为它是通过 `new String` 创建的包装对象，其原型链上包含了 `String.prototype`。同理，`objStr instanceof Object` 也返回 `true`。
- **数组与 null/undefined**：
  - **数组**：`const arr = []; arr instanceof Array` 返回 `true`（原型链上有 `Array.prototype`）。`arr instanceof Object` 也返回 `true`（`Array.prototype` 的原型是 `Object.prototype`，数组的原型链向上延伸到了 `Object` 原型对象）。
  - **null 和 undefined**：它们是没有原型链的原始类型。对它们使用 `instanceof` 总是返回 `false`（包括 `instanceof Object`）。尝试访问它们的原型时 JS 会报错。

## 5. 使用 instanceof 的注意事项与“坑” *Content-[15:44]

- **原型链被人为修改**：`instanceof` 完全基于对象和构造函数之间的原型链结构。如果通过 `__proto__` 属性或 `Object.setPrototypeOf` 等 API 人为修改或打破了原型链关系，`instanceof` 的结果将不再准确，不再符合对实例或继承的常规理解。
- **不能检测原始类型**：对 `string`、`number`、`boolean` 等基本类型使用 `instanceof` 都会返回 `false`。唯一的例外是使用包装类（如 `new String()`）创建的包装对象，它们是对象而非原始值，可以被检测。
- **跨 iframe（跨 Realm）问题**：
  - 在浏览器环境中，不同的 iframe 拥有各自独立的 JavaScript 运行时环境（Realm）。每个 Realm 有自己的全局对象和一套内置构造函数（如各自的 `Array`）。
  - 当从一个 iframe 获取一个数组对象，然后在父窗口或另一个 iframe 中使用 `instanceof Array` 检测时，可能会得到 `false`。因为接收方的 `Array.prototype` 和发送方数组原型链上的 `Array.prototype` 是两个不同的对象引用。
  - **解决方案**：在跨 Realm 判断类型时，推荐使用 `Object.prototype.toString.call(obj)`，它会返回形如 `[object Array]` 的字符串，该字符串值在不同的 Realm 中是一致的。
- **ES6 的 `Symbol.hasInstance`**：
  - 从 ES6 开始，可以在构造函数上定义一个名为 `Symbol.hasInstance` 的静态方法。
  - 如果构造函数定义了该方法，当使用 `instanceof` 检测时，JavaScript 引擎会优先调用并执行这个 `hasInstance` 方法，并将其返回值作为 `instanceof` 的结果，不再执行默认的原型链比对逻辑。
  - 这允许开发者完全自定义 `instanceof` 的行为，为对象和构造函数之间建立更加灵活的实例判断逻辑。

## 6. 课程总结与回顾 *Content-[19:44]

- **核心作用**：检测一个对象的原型链上，是否存在与某个构造函数的 `prototype` 严格相等的对象。
- **底层原理**：沿着对象的原型链向上查找，直到原型链顶端（`null`）或者找到匹配的原型对象。
- **关键注意事项**：
  1. 不能用来检测原始类型。
  2. 原型链可能会被人为修改，导致结果失真。
  3. 存在跨 iframe（跨 Realm）失效的情况。
  4. 需注意 ES6 引入的 `Symbol.hasInstance` 对其默认行为的潜在影响。

## AI 总结

本文深入解析了 JavaScript 中 `instanceof` 运算符的底层原理与实际应用。`instanceof` 通过沿对象原型链向上查找，判断是否存在与构造函数 `prototype` 严格相等的原型对象，从而精准检测实例与继承关系。相较于 `typeof` 和 `constructor`，它在处理复杂对象时更为可靠。笔记详细剖析了其检测过程的伪代码实现，并通过继承示例、原始类型与包装对象的对比，展示了其在不同场景下的表现。同时，重点强调了使用时的四大注意事项：原型链被篡改的风险、无法检测原始类型、跨 iframe 环境下的失效问题（推荐改用 `Object.prototype.toString.call`），以及 ES6 引入的 `Symbol.hasInstance` 自定义行为机制。掌握这些细节能帮助前端开发者更扎实地理解 JS 原型链机制，编写出更健壮的代码。

---

## 文稿转写

哈喽大家好 我是方格 今天我们要深入探讨一个在JS开发中非常常用 而且关键的一个运算符叫instance of 它看似很简单 但是其实背后涉及到了JAVASCRIPT中 一个非常核心的概念 原型链 理解instead instance of的原理 将帮助我们更加扎实地掌握JAVASCRIPT 的对象和继承机制 那么在本期课程里 我们会一起学习几个关键问题 首先instance of到底是用来做什么的 它的作用和我们熟悉的type of 或者直接访问对象的constructor属性有什么区别 为什么在某些场景下 instance of更加可靠 更加常用 最后也是最重要的部分 我们会揭开它的背后的原理啊 看看他是如何在JS引擎内部工作的 然后还会聊一下啊 在使用instance of时 我们需要注意哪些坑 以及如何规避它们 好 我们开始吧 我们先建立对instance of的核心理解 简单来说 instance of这个运算符 它的主要作用就是检测某个构造函数的 prototype属性是否出现在某个对象的原型链中的 任何位置 所以它的本质是一个用来判断对象和构造函数 之间原型链关系的工具 那么为什么我们需要它呢 这要从JAVASCRIPT的类型判断说起 我们常用的type of运算符 在判断基本类型时表现的很好 但是对于复杂类型 特别是啊对象 它的区分度是不够的 比如啊type of一个数组或者是字面量啊 或者是一个对象 字面量他们都返回object 你就无法用type of去区分 去知道一个变量到底是数组还是普通对象 但是在实际的开发中呢 我们经常需要判断一个对象 是否由特定的构造函数创建 或者它或者它是否继承字某个特定的类 这时候就需要一个更精确的方式 你可能会想到想到使用constructor属性 比如err点constructor等于那个啊 艾瑞对象这个方法有时候可行 但是点constructor属性是可以被修改的 不如基于引擎底层原型链的instance of 来得更可靠一些 而instance of其实恰好弥补了这些不足啊 他是专门用来检测对象和构造函数之间的 一个基于原型的血缘关系的 instance of的语法非常直接嗯 左边是你要检测的对象 Object 右边constructor是你要来检测的构造函数 最终它会返回一个布尔值 如果是true的话 就表示这个object是construct的实例 或者它在它深层的原型链上 能找到与这个constructor 原型对象匹配的原型对象 而force就没有这种关系 那么我们呃理解哦 instance of的关键在于理解它的检测过程 这整个检测过程 实际上就是一个沿着对象的原型链进行的 循环查找 所以他从你额要找的那个对象自身的原型开始 自身原型开始 也就是那个object的的原型链 object点杠杠 PROTO去匹配吧 如果第一次匹配不上 他会额继续向上查找 访问当前对当前原型的原型 这个过程会一直持续下去 一直持续下去 直到访问到原型链的终点 Now 所以这就是呃它instance of它的一个检测过程 那么在沿着原神链向上查找的过程中呢 没访问到一个原型对象 Instance of 就会拿它与我们要检测的构造函数的原型 去比对 也就是呃在呃对象object的原型链上 从object啊杠啊 从object点杠杠PROTO到object点杠杠PROTO 杠杠PROTO 任何一个被访问到的原型对象 与检测的那个constructor的prototype属性去啊 如果这两个对象严格引的引用是严格相等的 也就是这个他们他们的比对结果为true 那么这个instance of就立刻返回true 表示找到了匹配关系 检测成功 如果沿着呃在沿着圆形链向上查找的过程中 一直找到了原型链的终点now 也就是说没有任何呃 没有在任何的一个object的原型 任何一层原型上去找到construct点 prototype和它严格相等的对象 那么instance就会instance of就会返回false 表示object不是constructor的实例 它们之间没有通过prototype去建立原型链的关系 那么为了帮助大家更好的理解这个过程 我们可以用一段伪代码去模拟它的原理 当然这只是为了解释概念 真实的of instance of是啊 JAVASCRIPT引擎内置实现的效率更高 看这段伪代码 我们定义了一个函数 去接收一个object和一个constructor两个参数 那么第一步呢我们要检测它的原型 这里使用了更加规范的一个object点 get prototype of这个方法 它的效果就等同于去访问杠杠PROTO这个属性 然后我们进入了一个无限循环 在我在这个循环内部 首先判断当前的哦原型PROTO是否为now 如果是 就表示已经便利到原型链的终点了 还没有找到 还没有找到结果 那么就只能返回false 如果匹配的啊 PROTO当前的plot to不是now 就将它和这个constructor点prototype 去进行严格的相等的比对 如果相等的话 就说明在原型链上找到了匹配的原型 直接就返回true 如果当前的原型既不是now 也不是和这个constructor点prototype相等 那么就更新它的原型链 让人原形跟PROTO属性 让它指向当前圆形的圆形去继续查找下一轮 好我们再看一个经典的事例啊 通过代码去加深一下理解 这段代码 首先定义了animal和dog这两个构造函数 dog构造函数内部用啊 通过animal点call 然后去实现一个属性的继承 那么关键在这 就为了让这个哦dog成为animal的子类 我们就通过object create啊 却建立了他们的原型链继承关系 这就使得dog的实例对象的原型的原型指向了哦 animal点prototype 紧接着呢我们修复了这个关系啊 去让这个啊普原始对象的构造函数指向dog本身 这也是比较常见的实践 然后我们就创建了dog和animal这两个实例 以及一些其他类型的变量 包括原始字符串 String 包装对象和数组 用来后续的测试嗯 接下来我们是 去检测他们的打印结果 首先看my dog的结果 首先my dog instance of dog 我们根据这个原理 instance of从这个my dog的啊原型链开始找 然后my dog点杠杠PROTO 正好是啊dog点prototype 所以就是符合预期的 就是啊这里返回true 紧接着这是啊instance of animal 这次instance of会继续往上查找 在这个啊dog点prototype上没有找到匹配的啊 animal点prototype 所以会继续往上 所以呃这时候网上就找到了这个animal 所以这时候呃 和animal这个它的它自animal点prototype 与自身是严格相等的 所以这个也是返回true 这就印证了这个instance of 能够检测原型链上的关系啊 最后这个object也是继续沿着这个圆形链向上 经过dog和animal 最终达到这个圆形链的顶点 也就是object点prototype 然后呃 然后我们检测这个object点 PROTAPE与自身是严格相等的 所以instance of也返回true 这些事实都啊符合所有对象啊 都最终继承至这个object 它也反映了这个事实啊 然后接下来我们看原始类型和包装对象的例子 这是一个容易混淆的地方 接下来看原始类型和包装对象的例子 这是一个容易混淆的地方 我们有一个原始字符串 STR和通过啊new字符串创建了一个object string 然后呢呃这个结果strs str instance of string 它的结果是false 为什么呢 因为原始类型是没有原型链的 它不是他们不是通过构造函数去创建的对象 所以instance of啊 他试图访问SSTR点杠杠PROTO 他就会得到一个undefined或者引发错误 他自然就找不到这个string点prototype的原型对象 而object string instance of string 结果就是true 因为object属性啊 object string是通过new string创建的包装对象 它的原型链上包含了string点prototype 所以这步的结果就显示true 那么同理呢 Objects string instance of a object 因为它的原型链也包含啊object的原型对象 所以这一条也是返回true的 然后接下来再看一个例子啊 最后看看这个ERRY以及now和undefined的情况 err AI instance of err的结果是true 因为啊这个空数组是error构造函数的实例 它能够访问到它的 它的它的原型链上能够找到err点 Prototype every点instance of啊 object它的结果也是true 正如我们前面说的 errodent prototype的原型是object点prototype 所以数组的原型链也向上延伸到了 这个object的原型对象上 而对于now或者undefined来说呢 他们都是原始类型 且没有原型链 所以对它们使用instance of总是返回false 无论你检测什么样的构造函数 这里检测object同样是false啊 然后呃 在尝试访问这个 now或者undefined的原型的时候呢 JS会报错 那么理解了原理之后 我们来看看instance of啊 使用时需要注意哪些关键点 首先我们强调的就是instance of 完全基于对象和构造函数之间的原型链结构 那么这就意味着啊 如果 如果原神链被人人为的修改 比如通过修改这个呃杠PROTO属性 或者使用set prototype of这样的API 去修改或者打破这种关系 那么instance of的结果可能就不会再准确了 不会不会再符合你对实力或者继承的常规理解 那么第二个重点 我们刚才也在例子里看到了 instance of不能用来检测原始类型 包括 包括string啊 number啊 BULIN啊 这些基本的类型 对他们使用instance of都会返回false 唯一例外的就是你使用包装类包装对象 比如说使用new string去创建新的对象 它的它们是对象 而不是原始值 是可以被instance of检测的 那么第三个坑就是 跨六有的情况 或者是IPH 那么在浏览器环境中啊 不同的IPHRA就拥有各自独立的JASCRIPT 运行时环境 也就是所谓所谓的ram 每个ram都有自己的全局对象 自己的一套内置构造函数 比如说他们有各自的every构造构造函数 当你从一个IPHONE获取一个数组对象 然后在副窗口或者另一个IPHRAME中 使用instance of 去检测它是不是ERRY的实力的时候 就可能会得到false 因为接收方的error 构造函数的prototype和发送方的那个数组对象 原型链上的error点prototype是两个不同的对象 引用在这种跨ram判断类型的时候 通常会推荐一个更可靠的方法 比如object点prototype 点TOSTRING 点call这个object 它会返回一个形如啊 一个数字符 数组字符串嘛 叫前面是一个object 然后后面是个error 这个字符串值在不同的ring中是一致的 最后一个注意事项是一个比较现代的特性 叫symbol点 has instance呃 从es6开始 你可以在一个构造函数上 定义一个名叫symbol点 has instance的静态方法 如果构造函数定义了这个方法 那么当使用instance of检测这个构造函数时 JAVASCRIPT引擎会优先调用并且执行这个has instance方法 并且把它的返回值作为instance of的结果 而不再执行默认的啊 原型链比对逻辑 这方 这允许我们开发者完全自定义instance of的行为 为对象和构造函数之间建立更加灵活的实例 判断的一个逻辑 好我们来快速回顾一下本期视频的重点 Instant of 这个运算符 它的核心作用就是检测一个对象的原型链上 是否存在 与某个构造函数的prototype严格相等的对象 它的原理就是沿着对象对象的原型链向上查找 直到圆形链顶端或者匹配到啊 找到匹配的原型对象 那么在使用时我们需要特别注意 它不能检测原始类型 原型链可能会被修改 还有跨ram的情况 以及啊es6引入的这个symbol点 has instance对他的行为的潜在影响 好以上就是啊instance of的原理 希望能够帮助大家去更加深入的理解 JS的原型和继承机制 去写出更健壮的代码 好感谢大家的观看 如果你觉得这个视频有帮助 别忘了三连分享 我们下期再见
