# 手写 JavaScript bind 实现笔记

## 目录
- bind 的概念与核心功能
- 手写 myBind 的核心思路
- 手写 myBind 代码实现解析
- 具体示例验证
- 使用 bind 的注意事项
- 课程总结
- AI 总结

## bind 的概念与核心功能 *Content-[01:07]

`Function.prototype.bind` 是 JavaScript 内置提供的方法，挂载在 `Function` 的原型链上，这意味着所有函数都能调用它。它的核心功能是**返回一个全新的函数**。

这个新函数主要实现了两个核心目标：

- **固定 `this` 指向**：在新函数被调用时，强制固定其内部的 `this` 指向指定的值。在 JavaScript 中，`this` 非常灵活，会根据调用方式（对象方法、独立函数、事件回调等）发生变化。这种不确定性在异步操作或事件回调中常导致 `this` 丢失。`bind` 允许在实际调用前明确指定 `this` 目标值，避免此问题。
- **偏函数应用（Partial Application）**：这是一种函数式编程概念，指通过固定函数的部分参数来创建并返回一个新函数。`bind` 允许在绑定 `this` 的同时传入额外参数，这些参数会作为最终调用时参数列表的前缀被固定下来。这使得代码更灵活、复用性更高。

**原生 API 签名**：
`function.bind(thisArg, arg1, arg2, ...)`
- `thisArg`：绑定的 `this` 值。
- `arg1, arg2, ...`：预设参数，排列在新函数接收到的任何参数之前。

## 手写 myBind 的核心思路 *Content-[04:47]

手写一个 `myBind` 方法，需要遵循以下核心思路：

- **挂载位置**：在 `Function.prototype` 上添加 `myBind` 方法，使所有函数都能调用。
- **返回新函数**：`myBind` 必须返回一个全新的函数，不能修改原函数。
- **调用原函数并绑定 `this`**：在返回的新函数内部，需要调用原始函数，并确保 `this` 指向 `myBind` 的第一个参数（`thisArg`）。
- **参数合并**：正确将 `myBind` 传入的预设参数，与新函数实际被调用时传入的参数合并，并传递给原函数。
- **处理 `new` 关键字**：特殊处理新函数通过 `new` 关键字作为构造函数被调用的情况，此时 `this` 的行为与普通调用完全不同。

## 手写 myBind 代码实现解析 *Content-[06:11]

### 基础定义与类型检查
首先在 `Function.prototype` 上定义 `myBind`，接收 `thisArg` 和剩余的预设参数（使用扩展运算符 `...args`）。
- 在 `myBind` 内部，`this` 指向调用该方法的原始函数，使用 `const originFunction = this;` 保存。
- 进行健壮性检查：如果调用对象不是函数，根据规范应抛出 `TypeError`。

### 创建返回的新函数
创建一个匿名函数 `boundFunction` 作为最终返回的新函数体。该函数使用 `...innerArgs` 捕获调用时传入的参数。

### 参数合并
根据 `bind` 规范，`bind` 时传入的预设参数在前，调用时传入的参数在后。
- 使用 `concat` 方法合并参数：`const totalArgs = args.concat(innerArgs);`

### 区分普通调用与 `new` 调用（核心难点）
在 `boundFunction` 内部，需要判断当前的调用方式：
- **判断条件**：使用 `this instanceof boundFunction`。如果为 `true`，说明是通过 `new` 关键字调用的。
- **`new` 调用逻辑**：
  - 忽略传入的 `thisArg`。
  - 将原始函数 `originFunction` 作为构造函数，使用 `new` 关键字调用：`return new originFunction(...totalArgs);`。
  - 这样会自动创建新对象，将其原型链指向 `originFunction.prototype`，并将 `this` 绑定到新对象上。
- **普通调用逻辑**：
  - 如果 `instanceof` 判断为 `false`，说明是普通函数调用。
  - 使用 `apply` 方法强制设置 `this` 指向并传入合并后的参数：`return originFunction.apply(thisArg, totalArgs);`。

### 原型链处理说明
原生 `bind` 作为构造函数调用时，会确保 `new boundFunction` 创建的实例能通过 `instanceof originFunction` 的检查。
- 在上述简化实现中，直接通过 `new originFunction(...)` 构造调用，`new` 操作符本身就会连接原型链，使得实例的原型链指向 `originFunction.prototype`，从而完美通过 `instanceof` 检查。
- 若要达到 100% 精准模拟（不依赖 `new originFunction`），需要更复杂的代码：让 `boundFunction.prototype` 继承自 `originFunction.prototype`，并修改 `constructor` 指针等。但示例中的简化方案在多数情况下足够且更易理解。

## 具体示例验证 *Content-[14:57]

### 示例 1：普通函数的 `this` 绑定
- 定义一个 `obj` 对象和一个 `greet` 函数（内部使用 `this.name`）。
- 调用 `greet.myBind(obj, 'Hello')`，返回新函数 `boundGreet`。
- 调用 `boundGreet()` 时，走 `apply` 分支，`greet` 内部的 `this` 强制指向 `obj`，输出预期结果。

### 示例 2：偏函数应用
- 调用 `greet.myBind(obj, 'Good morning,')`。
- 返回的新函数在后续调用时只需接收剩余参数（如 `'!'`）。
- 内部将预设参数 `'Good morning,'` 与调用参数 `'!'` 合并，传递给 `greet`，实现参数预设功能。

### 示例 3：`new` 调用场景
- 定义构造函数 `Person`，接受 `name` 参数。
- 调用 `Person.myBind({name: 'ignore'}, 'defaultName')`，返回 `boundPerson`。
- 使用 `new boundPerson('Bob')` 进行调用。
- **行为验证**：
  - 传入的 `thisArg` (`{name: 'ignore'}`) 被完全忽略。
  - 内部判断 `this instanceof boundFunction` 为 `true`，走 `new originFunction` 分支。
  - 成功创建新的 `Person` 实例，`name` 为 `'Bob'`。
  - `personInstance instanceof Person` 为 `true`。
  - `personInstance instanceof boundPerson` 也为 `true`（因为原型链正确连接）。

## 使用 bind 的注意事项 *Content-[19:41]

在实际使用原生 `bind` 时，需牢记以下关键特性：

- **不修改原函数**：`bind` 总是返回一个全新的函数实例。每次调用 `bind` 即使参数相同，也会得到不同的函数对象。
- **多次 `bind` 无效**：一个已经被 `bind` 过的函数，无法再次使用 `bind` 改变其 `this` 或预设参数。新的 `bind` 调用总是会被忽略，这避免了 `this` 被层层绑定导致的混乱。
- **`thisArg` 为 `null` 或 `undefined`**：
  - 非严格模式下：原始函数内部的 `this` 会被自动替换为全局对象（浏览器中通常是 `window`）。
  - 严格模式下：`this` 会保持为 `null` 或 `undefined`。
- **`thisArg` 为原始类型**：如果传入的是字符串、数字、布尔值等原始类型，在原始函数被调用时，这些值会被自动包装成对应的对象（如 `String`、`Number`、`Boolean`）。
- **`new` 调用的特殊行为重申**：
  - `bind` 时传入的 `thisArg` 会被完全忽略。
  - 新函数内部的 `this` 指向 `new` 操作符刚创建的新对象实例，而不是 `bind` 指定的 `thisArg`。
  - `bind` 的预设参数和 `new` 调用时实际传入的参数会正常合并传递给原函数。

## 课程总结 *Content-[22:06]

- `bind` 方法返回一个全新的函数，携带了预设的 `this` 指向和参数。
- 手写 `bind` 的核心在于：在返回的新函数内部，区分普通调用和 `new` 调用，并采取不同策略调用原函数。
- 正确合并预设参数与实际调用参数，以及在 `new` 场景下处理 `this` 指向变化和原型链继承，是实现的关键点和挑战。
- 手写 `bind` 能加深对 JavaScript 中 `this`、参数处理及函数调用机制的深刻理解，强烈建议动手实践。

## AI 总结

本视频详细讲解了 JavaScript 中 `bind` 方法的核心原理及手写实现方案。笔记涵盖了 `bind` 的两大核心功能（固定 `this` 指向与偏函数应用），并逐步拆解了手写 `myBind` 的代码逻辑。重点剖析了参数合并机制以及最易出错的 `new` 关键字调用场景（通过 `instanceof` 判断并忽略 `thisArg`）。此外，还补充了原生 `bind` 在实际应用中的边界情况（如 `null/undefined` 处理、原始类型包装及多次绑定失效等）。这是一份非常全面的前端面试“八股文”实战指南，掌握手写 `bind` 能够显著提升对 JS 函数执行上下文和原型链的理解深度。

---

## 文稿转写

Hello 大家好 我是方格 欢迎来到今天的JS系列分享 在前端开发中 ban的方法是处理DISS指向和函数参数 非常常用的工具 虽然每天都在用 但是你是否好奇它内部究竟是如何工作的呢 今天我们就来一起揭秘BD的实现原理 并且尝试亲手写一个简单的模拟实现 那么在接下来的时间里 我们会一起探索几个核心问题 首先我们会明确明确BD的定义 去理解它的实现 然后呢 我们将深入模到模拟实现代 BD的核心逻辑里去啊 一步一步地去构建我们的代码 最后我们会讨论并且处理 band的在不同场景下的复查行为 特别是参数的合并以及如何应对啊 比如说使用new关键字 调用bind返回的函数的情况 首先我们来理解BD的概念 function点prototype 点bind 它是JAVASCRIPT内置的提供的一个方法 挂载在function的原型链上 这就意味着所有函数都能调用它 它的核心功能 用最简单的话来说就是返回一个全新的函数 那么这个新函数有什么特别之处呢 它主要实现了两个核心目标 第一个也是最常见的用途 就是在新函数被调用时 强制固定它内部的DISS指向到我们的值 第二它能够帮助我们预设一部分函数的参数 那么接下来我们会具体解释这两点 首先我们为什么要固定DISS呢 这是因为在JAVASCRIPT中DISS关键字是非常灵活的 它会根据函数的不同调用方式而发生变化 比如作为对象方法调用的啊 独立函数调用或者作为事件监听器回调时 DISS的值可能完全不同 所以这种不确定性 尤其是在异步操作的is 异步操作回调事件回调函数或者事件处理中 经常会导致DISS指向丢失的问题 难以访问到我们期望的对象属性或者方法 bin的方法的核心价值之一就在于 它允许我们在函数被实际调用之前 就明确的指定他的DISS目标值 从而避免了这些DISS丢失的坑 BD的另外一个重要能力就是实现偏函数应用 偏函数应用是一种函数式编程的概念 它指的是是通过固定函数的部分参数来创建 并且返回一个新的函数 ban的方法 允许你在绑定DISS的同时传入额外的参数 这些参数会最作为最终调用时 参数列表的前缀被固定下来 这样我们就可以基于一个通用的函数 创建出一个一些更具体更少参数的新函数 使得代码更加灵活 复用性更高 尽管我们是本节课聊的是手写实现 但是了解原生API是基础原生的by的方法 他的签名大概长这样 function点bind啊 然后啊这是啊diss argue 它就会这diss argue就绑定了我们的DISS值 然后这里有一堆的预设参数嗯 他就是会排列在啊线函数 接收到任何参数之前去 首先那我理解了这个API的写法之后 我们就知道手写需要模拟哪些行为了 我们先构思一下手写的实现 手写一个my band啊 我们需要遵循几个核心的思路 首先我们需要在function 点prototype上去添加一个新的方法 叫my b这样所有函数都能调用它 其次my b的方法必须返回一个全新的函数 这一点至关重要 因为band的不会修改原函数 接着呢在这个返回的函数内部 我们需要找一种呃方式来调调用原始的函数 在调用原函数时 要确保DISS指向是我们通过my band的第一个参数 指定的 This is argue 同时需要正确的将my bad传入的预设参数 和原和新函数实际被调用时 传入的参数合并起来并传递给原函数嗯 最后也是一个比较tricky的地方啊 我们需要特殊处理 当新将这个新函数不是通过普通调用 而是通过new关键字呃 作为构造函数被调用的情况 因为在这种情况下 DISS的行为会和普通调用完全不同 好我们开始写代码 首先我们在呃 function点prototype上去定义一个my band的方法 它接收啊 diss argue作为第一个参数以及剩余的参数 我们用扩展运算符点点点argues 来方便地获取到这些预设的参数呃 在这里my bad方法内部的DISS指向的是什么 指向的就是调用我们my band的这个方法 本身的函数 也就是我们的原始函数 所以在这里我们用一个变量origin function 把这个DISS保存起来 以便在后续新函数内部调用 然后接着呃 为了这让这个代码更健壮 我们需要检查一下my band的对象是否存在 是否确实是个函数额 如果调用对象不是函数的话 根据规范应该抛出一个type error 那么BD的核心就是返回一个新的函数 所以我们在这里呃 在后面需要呃创建一个匿名函数啊 去创建一个新的函数 并且啊赋值给这个B的方CTION这个变量 这个BFUNCTION就是我们最终要返回给新函数的 一个函数题 呃 那么这个函数呢同样的也可以接收自己的参数 我们用in the argue去捕获它们 当这个B的方式被调用时 它内部的代码快就会执行啊 在BG方CTION函数体内部呢 DISS的值取决于BD的这个function的调用方式 我们的任务就是在这个地方 确保原始函数origin function被调用时 它的DISS指向以及参数都是正确的啊 正如前面所说啊 呃这个my band的返回值 就是这个新创建的B的放CTION 现在我们来到这个新的函数BT方式内部 当当function被调用时 它会接收到一些参数 就是我们的啊 就是我们的用这个inner argues去捕获的 我们需要我们需要将这个my band 第一次传入的那些预设参数 argues和预设参数argues 和我们这次调用ban function传入的inner agules 去把它们啊合并起来 最终形成最终形成我们啊 要传递给这个原始origin function的一个参数列表 根据band的规范 band的时传入的参数应该在前面啊 B的额ban的方法呃 调用时传入的参数在后面 所以我们在使用这个contact的方法 将这个argues和in the argue合并存入变量 然后接下来呢就是处理bind的实现中 最容易出错 也是最关键的部分 当band的返回的这个binder function不是普通方式调用 而是通过new关键字作为构造函数被调用时 他的行为会发生显著的变化 在这种情况下呢 我们呃band的传入的dis argue会被完全的忽略 新函数内部的DISS会指向这个new操作符 自动创建的这个一个新的实例 instance啊 我们就可以用这个this instance of帮方迅去检查 去检查来判断当前的band是否调当年的B的方 CTION是否调用了new关键字 如果使用了new diss就会丢 就会是这个bound function的一个实例 所以这个判断为true 就会走到这里 如果啊 那么这时候呢我们就不在这 Instance 就不再使用这个diss argue了 此时应该将这个原始的orion function 作为一个构造函数 然后使用new关键字来调用它 并且把合并后的total argues全部全部传进去 这样做就会自动创建一个新的对象呃 把它的并且将它的原原型链指向这个origin function 点prototype 并且把alligent function函数体里的那个DISS 绑定到这个新的对象上 执行初始化代码 new调用默认会返回这个新创建的对象实例 所以我们可以直接返回啊 new new function的new origin function的结果 嗯如果this n this instance of判断为false 这就意味着什么 这就意味着嗯 这就意味着 棒子方式是通过普通函数的方式被调用的 好在这种情况下 我们就需要执行普通函数的调用逻辑 我们我们需要啊使用这个bind方法的第一个 第一次传入的这个diss argue 来强制设置原始的origin function去的DISS 指向调用函数 并且指向DISS的和参数的方式有很多 这里我们选择使用apply apply接收两个参数 第一个参数是需要绑定的DISS值 第二个参数是一个数组 包含需要传递给函数的参数 apply会他就会立即执行origin function 并且返回它的结果 所以我们直接返回啊这个apply的结果即可 最后就是稍微提一下原型链的处理呃 在原生的band的作为构造函数调用时 会确保new by the function创建的实例能够通过instance of嗯 origin function的检查 这是因为new操作符本身就会连接原型链 我们前面的模拟实现中呢 处在处理new调用时 是直接通过啊new origin function来构造调用啊 原函数的构造行为的 这样做的巧妙之处就在于 new origin function创建的对象 实例的那个原型链会指向origin function的原型对象 而在判断this instance of b方CTION时 虽然使用了帮子方CTION 但是最终实例通过PROTOTY 刚刚 PROTO链是可以回溯到origin function 的一个原型对象上的 所以他完全啊 因为完全模精准模拟 原生BD作为构造函数时的原生链行为 其实他其实如果要完成精准模拟的话 就需要更复杂的代码来保证binder function prototype继承自这个origin点prototype 并且要修改这个constructor这个指针等等 我们示例中啊 new origin function的方案在很多情况下其实是足够的 并且更容易理解 所以这里啊我们使用了更简单的new的方案 好理论讲完了 我们再看一些具体事例 我们用我们手写的my band去验证他们 首先是普通函数的DISS绑定 我们这里有一个object对象 一个grade函数 它内部使用了DISS点name和啊diss ant name啊 这两块代码我们调用great点my bind嗯 然后将object作为的DARGUE传到这个函数里面 并且预设了第一个参数 Hello 这时候就会返回一个普通的新的函数 叫bound great 当我们调用这个BGAY感叹号时 这个my bad返回的新函数内部逻辑会执行啊 因为是普通函普通的调用 所以会走那个之前的applied分支 所以嗯 此时grade函数内部的DISS 就会强制设置成这个object 然后所以参数是hello I am alice 然后我们再看一个例子啊 这是一个偏函数应用的例子 还是同样的一个object和一个grade函数 这次我们调用great点mind band object 然后这里传了good morning和逗号 啊除了绑定DISS和呃 除了绑定和DISS和为object 我们还预设了这两个参数嘛 所以在返回的啊 这个新函数后续只需要接收后续的参数呃 我们在这里调用了一个接收了一个感叹号 在新函数的内部 my band的argues good morning 和调用时的in the argues 一个感叹号就会被合并成嗯 Good morning 逗号感叹号 然后通过apply传递给grade函数 并且最终输出 Uh good morning I am alice 最后再来啊看一个new调用的例子 这里这时候呢 呃有个我们有一个简单的构造函数person 他接受一个name参数 并且赋值给这个diant name 我们对这个my person进行my band的调用 传入一个参数 传一个对象作为DISARGUES 注意这里我们传的是啊name ignore啊 然后在new调用时 这个这个DIARGUE是会被忽略掉的 这个name ignore是会被忽略掉的 我们通过new bound person 这个bob来调用这个返回的啊 新函数bounder person嗯 此时呢因为根据我们的BD的内部逻辑啊 会判断它是new调用的 因为DISS点instance of这个bounder function是true 然后就会去执行这个new origin function嘛 也就是new person new了一个新的人叫做bob 所以最终一个新的person实例就会被创建 它的name是person嗯 所以输出这个person instance点name就会得到bob 然后并且呢我们是啊new调用了嘛 所以啊 所以这里的话我们person instance of person Person instance instance of person应该是true 同时呢实力应该也呃也实力 也是通过这个new帮帮person创建的 所以person instance of instance啊 bd person也应该是true 所以这些都验证了我们对调啊 new调用场景的模拟是基本符合这个原生行为的 在实际使用呃B的时 有些关键的注意事项需要牢记 第一就像我们前面强调的B的不修改原函数 它总是返回一个最新的函数实例 每次调用bind 即使参数完全相同 你也会得到一个不同的函数对象 更重要的是一个已经被ban过的函数 你无法再使用啊 band来改变它的DISS或者预设参数 新的BD调用总是会被忽略的 还是这是原生BD的一个重要特性 这就避免了DISS被成绳绑定导致的一个混乱 啊第二个注意事项是关于DARGUE的处理嗯 当bend的第一个参数 DISARGUE是now或者undefined 是在非严格模式下 原生原始内部 原始函数内部的DISS会被自动替换成全局对象 在浏览器环境通常是window 但是在严格模式下 DISS会保持为now或者undefined 此时如果迪斯阿迪斯argue是一个啊 此外呢就是如果diss argue是个原始类型的值 比如字符串数字布尔值 原始函数调用被调用时 这些原始值就会被自动包装成对应的对象 比如string啊 number啊 bully啊 嗯最后一个关键点再次强调就是band返回的函数 通过new调用时的特殊行为 首先band的时传入的diss argue会被完全忽略 其次新函数内部的DISS会指向diss new操作符 刚刚创建的新对象实例 而不是by的 是指定的diss argue 最后band的预设的参数和new调用时 实际传入的参数会合并到一起 作为参数传递给原函数 好我们对啊手写BD的探索就到这里 简单总结一下bind的方法 返回一个全新的函数 这个新函数携带了预设的DISS指向和参数 手写band的的核心在于 在我们返回的新函数内部 需要具备区分普通调用和new调用的能力 并且根据不同的调用方式 采用不同的策略去调用原始函数 正确合并伴的传入的预设参数和 新函数被调用时传入的参数 以及在new调用场景下 处理DISS指向的特殊变化和原型链继承 是实现这个band的方法的关键点和挑战 通过手写band的呢 我们会加深对BN的工作原理的理解 也对JS中DISS参数处理以及函数调用啊 有会有更加深刻的认知 所以我推荐大家都去啊手写实践一下 好感谢大家的观看 希望这次分享对你有所帮助 如果喜欢的话 欢迎点赞分享 也欢迎在评论区留言讨论 我是方格 我们下期再见
