## 目录
- 第一章：建立对 this 的正确认知
- 第二章：决定 this 指向的四条核心规则
- 第三章：箭头函数与规则优先级总结
- 第四章：经典面试题与实战解析
- 第五章：核心总结
- AI 总结

## 第一章：建立对 this 的正确认知 *Content-[01:13]*

在 JavaScript 开发中，`this` 关键字的指向是让许多开发者（尤其是初学者）感到头疼的核心问题。要彻底搞懂 `this`，首先需要建立以下正确认知：

- **什么是 `this`**：它是 JavaScript 中的一个特殊关键字，本质上是一个特殊的对象引用。
- **运行时绑定**：`this` 的值**不是**在函数定义时决定的，而是在函数被真正调用时才确定下来。
- **调用点决定**：`this` 具体指向谁，完全取决于函数的调用方式（即调用点）。

**为什么不能绕开 `this`？**
1. **面向对象编程的基石**：无论是使用构造函数还是 ES6 的类（Class），都离不开 `this`。
2. **处理回调函数**：在事件监听、定时器（如 `setTimeout`）中，`this` 的指向极易丢失，理解它才能解决常见的 Bug。
3. **深入理解框架**：像 React 这样的前端框架，其内部原理大量使用了 `this`。
4. **面试必考**：这是前端面试中几乎必考的核心知识点。

## 第二章：决定 this 指向的四条核心规则 *Content-[03:16]*

决定 `this` 指向的规则共有四条，我们将按照优先级**从低到高**的顺序进行深入学习。

### 1\. **规则一：默认绑定** *Content-[03:30]*

这是最基础的规则。当没有其他任何规则适用时，就会触发默认绑定。

- **触发条件**：函数被独立调用（如直接调用 `foo()`），没有任何上下文对象。
- **非严格模式**：`this` 指向全局对象（在浏览器中为 `window`）。
- **严格模式**：为了安全起见，如果在文件顶部加上 `"use strict"`，`this` 会是 `undefined`。

**代码示例**：
```javascript
function sayHi() {
  console.log(this);
}
sayHi(); // 非严格模式打印 window，严格模式打印 undefined
```

### 2\. **规则二：隐式绑定与隐式丢失** *Content-[04:45]*

隐式绑定的优先级高于默认绑定，在日常开发中非常常见。

- **触发条件**：函数作为对象的方法被调用时（如 `obj.method()`）。
- **指向规则**：`this` 会指向调用该方法的那个**对象本身**。

**代码示例**：
```javascript
const user = {
  name: 'Alice',
  greet: function() {
    console.log('Hello ' + this.name);
  }
};
user.greet(); // 打印 "Hello Alice"，此时 this 指向 user 对象
```

**⚠️ 隐式丢失陷阱**：
当我们将对象的方法赋值给另一个变量，然后通过新变量独立调用时，`this` 的指向就会丢失，退回到**默认绑定**规则。
```javascript
const standAloneGreet = user.greet; // 仅赋值，未调用
standAloneGreet(); // 独立调用，丢失 user 上下文
// 非严格模式下 this 指向 window，打印 "Hello undefined" (或空字符串)
// 严格模式下 this 为 undefined，尝试读取 undefined.name 会抛出 TypeError
```

### 3\. **规则三：显式绑定 (call, apply, bind)** *Content-[07:37]*

如果我们希望精确控制 `this`，防止其意外丢失，可以使用显式绑定。通过 `call`、`apply` 和 `bind` 可以强制指定函数调用时 `this` 的值。

- **`call`**：立即调用函数，`this` 指向第一个参数。后续参数逐个传递。
- **`apply`**：立即调用函数，`this` 指向第一个参数。唯一的区别是第二个参数必须是一个**数组**，包含函数需要的所有参数。
- **`bind`**：**不会立即调用函数**，而是返回一个全新的函数。这个新函数的 `this` 会被永久绑定到 `bind` 的第一个参数上（这种方式称为**硬绑定 Hard Bind**）。

**代码示例**：
```javascript
function introduce(city, country) {
  console.log(`I am ${this.name} from ${city} ${country}`);
}
const person = { name: 'Bob' };

// 1. call：参数逐个传递
introduce.call(person, 'New York', 'USA'); 

// 2. apply：参数以数组形式传递
introduce.apply(person, ['Paris', 'France']); 

// 3. bind：返回新函数，永久绑定 this
const boundIntroduce = introduce.bind(person);
boundIntroduce('Paris', 'France'); // 打印 "I am Bob from Paris France"
```

### 4\. **规则四：new 绑定** *Content-[10:40]*

这是优先级最高的规则。

- **触发条件**：使用 `new` 关键字调用一个函数（即把它当做构造函数使用）。
- **指向规则**：`this` 会指向由 `new` 命令创建出来的**全新的空对象**。

**`new` 关键字背后的四个步骤**：
1. 创建一个全新的空对象。
2. 将这个新对象的原型（`__proto__`）链接到构造函数的 `prototype` 上。
3. 将这个新创建的对象绑定为这次函数调用的 `this`。
4. 如果该函数没有自己返回一个其他对象，那么 `new` 表达式会自动隐式返回这个新创建的 `this`。

**代码示例**：
```javascript
function Person(name) {
  this.name = name; // 给新创建的对象设置属性
}
const alice = new Person('Alice');
console.log(alice.name); // 打印 "Alice"
```

## 第三章：箭头函数与规则优先级总结 *Content-[12:43]*

### 1\. **箭头函数的 this 机制** *Content-[12:49]*

ES6 引入的箭头函数在 `this` 的处理上完全颠覆了之前的规则。

- **没有自己的 `this`**：箭头函数不绑定 `this`。
- **词法作用域决定**：它的 `this` 会捕获**定义时**所在词法作用域的 `this`。也就是说，箭头函数在写出来的那一刻，`this` 指向就已经决定了。
- **不可修改**：之后再也无法通过 `call`、`apply` 或 `bind` 来修改箭头函数的 `this`。

**代码示例**：
```javascript
const obj = {
  name: 'my object',
  regularMethod: function() {
    console.log(this.name); // 隐式绑定，打印 "my object"
    
    const arrowFunction = () => {
      // 箭头函数继承外层 regularMethod 的 this
      console.log(this.name); // 打印 "my object"
    };
    arrowFunction();
  }
};
obj.regularMethod();
```

### 2\. **箭头函数的常见误区** *Content-[15:08]*

很多初学者会直接在对象字面量中使用箭头函数来定义方法，这是一个必须避开的坑。

```javascript
const obj = {
  name: 'my object',
  arrowMethod: () => {
    console.log(this.name); 
  }
};
obj.arrowMethod(); // 打印 undefined
```
**原因分析**：这个箭头函数并不是在某个普通函数内部定义的，而是直接定义在**全局作用域**中。因此，它捕获的是全局作用域的 `this`（即 `window` 对象）。`window` 上没有 `name` 属性，所以打印 `undefined`。

### 3\. **四条规则优先级总结** *Content-[16:13]*

当分析一个 `this` 指向时，可以按照以下顺序（从高到低）来判断它命中了哪条规则：

1. **`new` 绑定**（最高优先级）
2. **显式绑定**（`call`, `apply`, `bind`）
3. **隐式绑定**（作为对象的方法调用）
4. **默认绑定**（独立调用，全局或 `undefined`）

## 第四章：经典面试题与实战解析 *Content-[16:51]*

**题目**：在 `setTimeout` 定时器中使用对象方法，`this` 会指向谁？应该如何修正？

**场景代码**：
```javascript
const myTimer = {
  seconds: 100,
  start: function() {
    setTimeout(function() {
      console.log(this.seconds);
    }, 1000);
  }
};
myTimer.start();
```

**问题分析**：
`setTimeout` 接收的回调函数在一秒后会被 JavaScript 的事件循环机制取出来**独立调用**。此时它没有任何上下文对象，完全丢失了 `myTimer` 的上下文，触发了**默认绑定**规则。`this` 指向 `window` 或 `undefined`，尝试访问 `this.seconds` 会打印 `undefined` 或直接报错。

**修正方案**：

**方案一：使用显式绑定 (`bind`)**
在传递回调函数时，使用 `.bind(this)` 将 `this` 永久绑定。这里的 `this` 在 `start` 方法中指向 `myTimer`。
```javascript
setTimeout(function() {
  console.log(this.seconds);
}.bind(this), 1000);
```

**方案二：使用箭头函数（推荐）**
将回调函数换成箭头函数。箭头函数没有自己的 `this`，会捕获定义时所在的作用域（即 `start` 方法中的 `this`），代码更加简洁。
```javascript
setTimeout(() => {
  console.log(this.seconds); // 正确打印 100
}, 1000);
```

## 第五章：核心总结 *Content-[19:21]*

1. **动态绑定**：`this` 是在函数被调用时，由调用方式决定的，这是一个动态的运行时绑定过程。
2. **优先级法则**：牢记四条绑定规则的优先级：`new` 绑定 > 显式绑定 > 隐式绑定 > 默认绑定。
3. **箭头函数特例**：箭头函数的 `this` 由定义时的词法作用域决定，并且不可更改。它是解决回调函数中 `this` 丢失问题的现代最佳实践。

## AI 总结

本视频系统讲解了 JavaScript 中 `this` 关键字的核心机制。首先明确了 `this` 是运行时绑定，由函数的调用方式（调用点）决定。接着详细剖析了决定 `this` 指向的四条规则：默认绑定、隐式绑定（及其丢失陷阱）、显式绑定（`call`/`apply`/`bind`）以及优先级最高的 `new` 绑定。随后，重点讲解了 ES6 箭头函数的特殊性——其 `this` 由词法作用域决定且不可修改，并指出了在对象字面量中误用箭头函数的常见陷阱。最后，通过 `setTimeout` 的经典面试题，展示了如何利用 `bind` 或箭头函数解决回调中的 `this` 丢失问题。掌握这些规则与优先级，是应对前端面试和复杂开发场景的关键。

---

## 文稿转写

Hello 各位学前端的小伙伴 欢迎回到方格的JS课堂 今天我们要攻克一个让很多JSK开发者 尤其是初学者感到头疼的问题 就是DISS的关键字 DISS究竟指向谁 这是一个在面试和实际开发中 都无法回避的核心问题 那么这节课呢我们就把它彻底搞明白 在接下来的内容里呢 我们会一起探讨几个这样的核心问题啊 首先我们DISS的值到底是在什么时候被确定的 其次我们会深入学习啊 决定DISS指向的四条核心绑定原则 再接着我们会专门分析啊 es6中箭头函数的DISS为什么如此的与众不同 最后呢我们会通过一个经典的面试题 把学到的知识应用起来 让你能够从容地应对各种复杂的场景 好让我们正式开始 首先第一章我们来建立对DISS的正确认知 那么到底什么是DISS 简单来说它是一个drop skip的关键字 也就是一个特殊的对象引用 理解DISS有几个关键点 你必须记住 第一也是最重要的一点 DISS是运行时绑定的 这就意味着DISS的值不是函数定义时决定的 而是在函数被真正调用时才确定下来啊 第2DISS具体指向谁 完全取决于函数的调用方式 我们称为啊调用点 记住这两个核心原则 是理解后面所有规则的基础 那么有些同学可能会觉得DISS那么复杂 我能不能绕开它 答案是几乎不可能了 首先DISS是面向对象编程的基石 无论是用构造函数还是类都离不开它 其次在处理回调函数 比如事件监听定时器 DISS的指向就很容易丢失 理解它才能解决这些常见的bug 再者如果你想深入理解像react这样的前端框架 你会发现它们的内部原理也大量地用到了DISS 最后呢 他也是前端面试中几乎必考的核心知识点 所以重要性是不言而喻的 好有了这些基础的认知之后呢 我们进入第二章 也就是本集最核心的部分 决定DISS的指向的四条规则 我们会按照他们的优先级来从低到高的学习啊 首先第一条规则叫默认绑定 这是最基础的规则 当没有其他任何规则适用时 就触发它 具体来说当一个函数被独立调用时 比如CH这样直接调用在非严格模式下 DISS就会指向全局对象 在WINDO在浏览器里就是window 而在严国模式下呢 为了安全 DISS会是undefined 我们来看一个简单的例子 这里我们定义了一个say hi函数 函数体里只有一行consulted log diss 然后我们在这里直接调用它 这个调用方式非常普通 没有任何的上下文对象 因此它命中了我们的默认绑定的规则 所以在非严格模式的浏览器控制台里 你会看到打印出window对象 如果你在文件顶部加上一个use strict 那么打印出来的就是undefined啊 第二个规则叫影视绑定 他的优先级高于默认绑定 这条规则非常常见 当函数作为一个对象的方法被调用时 就会触发它 此时呢DISS会指向调用这个方法 那个的那个对象本身 来看这个例子 我们创建了一个user对象 他有一个name属性和great方法 关键看这里啊 我们是通过这个user点great的方式 去调用这个函数的 注意 这个调用形式函数great 是被user这个上下文对象拥有和调用的 因此呢根据影视绑定规则 在grade函数内部 DISS就指向了user对象 所以DISS点name就等于user点name 最后会打印出hello Alice 影视绑定有一个非常重要的陷阱叫隐视丢失 这指的是当我们将一个对象的方法 赋值给另外一个变量 然后通过这个新变量独立调用时 DISS的指向就会丢失 退回到我们刚才讲的第一条规则 默认绑定 好好看 第一行 我们把user点great这个方 这个方法赋值给了这个standard啊 great这个新变量 注意啊 这里只是赋值 并没有调用函数 这个变量现在直接引用了这个grit函数本身 然后我们再看第二行 我们调用了这个对象 这个变量 你看这个调用方式 是不是和我们默认绑定的例子一模一样 它是一个独立的函数调用 没有任何的上下文对象 所以user的上下文丢失了 那么结果是什么 结果就是在非严格模式下 DISS指向全局对象 DISS等于name是个空字符串 所以打印hello 在严格模式下 DISS是undefined 尝试去读取这个undefined等name 就会直接抛出type error 这是开发中一个非常常见的错误来源 好如果我们不希望呃DISS意外丢失 想要精确控制它怎么办呢 这就引出了我们的第三条规则 显示绑定 我们可以通过call apply和bind 这三个方法来强制指定函数 调用时DISS的值 首先是点call 它会立即调用函数 并且将函数的DISS指向它的第一个参数 Dargue 如果函数还有其他参数 就依次跟在后面去传递 apply和call这个两个方法是非常类似的 apply也会立即调用函数 并且将这个DISS指向第一个参数 唯一的区别在于apply的第二个参数是个数组 所啊函数需要的所有参数都会放到这个数组里 最后是band band的 这是这三者中最特别的 因为他不会立即调用函数 相反的它会返回一个全新的函数 这个函数的DISS会被永久的绑定到嗯 band的第一个参数上 无论之后怎么调用这个新的函数 它的DISS都不会再改变 我们有时有把这种方式称为硬绑定 Hard brandy 我们再来通过一个例子把这三者串联一下啊 这里有一个introduce函数 它会打印DISS点name以及传入的城市和国家 还有个person对象 它只有一个name属性 然后我们使用call啊 introduce点call和person 这样呢 introduce内部的DISS就会被强制的指向了 person对象 后续参数逐个传入 会去打印出 i am bob from new york usa啊 然后看第九行 第八行我们使用apply啊 效果是完全一样的 只是参数的传递方式变成了数组 最后我们看bind 啊这个introduce点bind创建了一个新的函数 是这个变量啊 此时呢这个新函数的内部的DISS 已经永远是person了 所以呢我们直接调用这个新函数啊 并且传入参数 它就能够正确的打印出这个i am bob from paris france 然后第四条规则也是优先级最高的规则 叫new绑定 当我们使用new关键字来调用一个函数时 也就是把它当做构造函数使用 DISS会指向一个由new命令创建出来的 全新的空对象 一 嗯为了理解new绑定 我们必须知道new关键字在背后 默默做了哪四件事情 首先第一它会先创建一个全新的空对象 第二 这个新对象的原型 会被链接到构造函数的prototype上 第三也是最关键的一步 这个新创建的对象 会被绑定为这次函数调用的DISS 第四如果这个函数没有自己返回一个其他对象 那么new表达式就会自动的影视的返回 这个新创建的DISS 嗯我们用代码来验证一下 这里有一个person构造函数 当我们执行CONSTALICE等于new person alice时 这个new关键字就发挥了作用 那么在person s函数内部呢 一个空对象被创建 并且啊绑定给了DISS 所以DISS等于name等于name 这行代码实际上就是在给这个新对象 去设置一个name属性 然后函数执行完毕之后呢 这个新对象被隐式的返回 并且赋值给了ALICE变量 因此在第七行和第八行的consult点logo中 我们就能正确的打印出ALICE 好学完了四条核心规则啊 我们进入第三章 看一个非常特殊的存在箭头函数 并且梳理一下所有规则的优先级啊 那么箭头函数嗯是在es6引入的 他在电DISS的处理上完全颠覆了之前的规则 核心要点是箭头函数没有自己的DISS绑定 那么他的DISS从哪来呢 答案是他会捕获他定义时所在的词法 作用域的DISS 也就是说箭头函数在写出来的那一刻 他的DISS指向就已经决定了 并且之后再也无法通过call apply或者bind来修改 那么这个例子就能很好地说明问题啊 我们有一个object对象 它有一个regular method 这是一个普通的函数 当通过object点regular method调用时 根据我们学过的隐性绑定 影视绑定他的DISS就会指向这个object啊 所以第四行就会打印这my object 然后再看关键的部分 在regular method内部 我们定义了一个error alarrow function 箭头函数 根据箭头函数的规则 它没有自己的DISS 他会去寻找它 定义定义它时所在的作用域的DISS呃 这个箭头函数是在这个regular method 这个函数体里被定义的 所以regular metal的DISS正是指向object 所以箭头函数这个error function就继承了这个DISS 因此当这个函数被调用时 它内部的DISS同样的指向了my 指向了这个object 所以打印出来的也就是my object 这里有一个箭头函数常见的误区啊 很多初学者可能会这样写对象的方法啊 直接在这个对象字面量里去用啊 建造函数来定义啊 Erroarrow method 那么问题来了 这个箭头函数定义在哪个作用域里 它不是在某个函数内部被定义的对吧 而是在全局作用域中定义的 因此有个什么问题 它捕获的是全局作用域的DISS 也就是window对象 所以当调用object点arrow mescal的时候呢 DISS指向的是window window上没有name属性就会打印undefined 这是我们使用箭头函数必须要避开的坑 那么现在呢我们来总结一下 这四条规则的优先级从高到低 依次是第一new绑定 第二显示绑定 也就是call apply bind 第三隐式绑定 也就是作为对象的方法去调用 最后才是默认绑定全局或者undefined啊 当你分析一个DISS指向时 就可以按照这个顺序来判断它命中了哪条规则 好学完了理论啊 我们来看一道非常经典的面试题 在setting out这个里面去使用一个对象方法 DISS会指向谁 应该如何修正呢 啊看这段代码 我们有一个my timer对象 它有一个start方法 这个方法会在一秒后去尝试打印DISS点 Seconds 你觉得会发生什么 我们来分析一下 首先SETOUT这个定时器接收了一个回调函数 这个回调函数在一秒后会被呃 JASCRIPT的事件循环机制取出来 去独立的调用 那么这个调用方式呢没有任何的上下文对象 他完全的丢失了my timer的上下文 因此呢它触发了我们讲的第一条规则 默认绑定DISS会指向window或者undefined 尝试访问DISS点 seconds自然就会报错了 打印出note none 或者是啊undefined 或者是直接报错 那么如何修正呢 有两种主流的方案 方案一是使用我们写学过的显示绑定 在传递回调函数时 直接使用点band的DISS 这里的DISS是start方法的DISS 它指向my timer 我们通过呃band把这个DISS永久的绑定了 给了这个回调函数 问题就解决了 然后第二个也是我们比较推荐的方案 就是使用箭头函数啊 我们把这个回调函数换成箭头函数 箭头函数没有自己的DISS 它会捕获定义时所在的作用域 也就是start方法的一个中的DISS 所以这就是我们想要的效果啊 代码也会更加简洁 好我们最后来做个核心总结啊 第一DISS是在函数被调用时 由调用方式决定的 这是一个动态的运行时绑定过程 第二我们要牢记四条绑定规则的优先级啊 new绑定大于显示绑定 优先于隐式绑定啊 最后是默认绑定 第三箭头函数是一个特例 他的DISS由定义时的词法作用域决定 并且不可更改 它也是解决回调函数中 DISS丢失问题的现代最佳实践啊 希望通过这节课 你对DISS有一个系统而且清晰的认知 感谢观看 我是方格 我们下期再见
