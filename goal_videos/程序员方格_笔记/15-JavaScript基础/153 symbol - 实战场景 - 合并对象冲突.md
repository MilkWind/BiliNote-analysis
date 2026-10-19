## 目录
- Symbol 实战场景概述
- 场景一：解决对象属性名冲突问题
  - ES5 中的属性名冲突痛点
  - 使用 Symbol 解决属性冲突
  - Symbol 属性的访问与遍历
- AI 总结

## Symbol 实战场景概述 *Content-[00:00]

`Symbol` 的所有特性最终都是为了开发实战服务的。在企业开发中，`Symbol` 有四个高频次的使用场景，这些不仅是核心使用场景，也是前端面试中的高频考点。本系列笔记将详细拆解这四大实战场景，本节课重点讲解第一个场景：**解决对象属性名冲突的问题**。

## 场景一：解决对象属性名冲突问题 *Content-[00:18]

在 ES5 中，对象的属性名都是字符串。当我们在合并对象或者动态添加属性时，极其容易出现属性名冲突从而导致原有属性被覆盖的问题。而 `Symbol` 的值具有**唯一性**，可以从根本上解决这个冲突问题。

### ES5 中的属性名冲突痛点 *Content-[00:22]

在 ES5 中，如果两个对象拥有相同的属性名，在使用 `Object.assign` 合并时，后添加的属性值会覆盖先添加的属性值。

**代码示例与问题分析：**

```javascript
// 定义第一个对象
const obj1 = {
  title: 'JavaScript',
  description: '前端必备编程基础'
};

// 定义第二个对象
const obj2 = {
  description: '精于前端，专于面试'
};

// 使用 Object.assign 合并两个对象到空对象中
const obj = Object.assign({}, obj1, obj2);

console.log(obj);
```

**运行结果：**
- `title` 字段正常保留，值为 `'JavaScript'`。
- `description` 字段的值变成了 `'精于前端，专于面试'`。

**结论：** 
第 12 行 `obj1` 中的 `description` 被第 15 行 `obj2` 中的 `description` 成功替换（覆盖）。这就是 ES5 中由于属性名都是字符串而导致的典型覆盖痛点。

### 使用 Symbol 解决属性冲突 *Content-[03:06]

为了解决上述覆盖问题，我们可以使用 `Symbol` 作为属性名。因为即使两个 `Symbol` 的描述（description）完全相同，它们生成的值也是绝对不相等的。

**代码示例与解决方案：**

```javascript
// 1. 定义两个 Symbol 变量，描述都叫 'description'
const sym1 = Symbol('description');
const sym2 = Symbol('description');

// 验证唯一性：sym1 !== sym2 (两者完全不相等)

// 2. 将 Symbol 作为对象的 Key
const obj1 = {
  title: 'JavaScript',
  [sym1]: '前端必备编程基础' // 使用计算属性名语法
};

const obj2 = {
  [sym2]: '精于前端，专于面试'
};

// 3. 再次合并对象
const obj = Object.assign({}, obj1, obj2);

console.log(obj);
```

**运行结果：**
- 展开 `obj` 后，会发现 `sym1` 和 `sym2` 对应的两个字段**同时存在**，完美共存。
- 在控制台中，它们看起来长得一模一样（都显示为 `Symbol(description)`），但由于它们是 `Symbol` 类型，底层完全不相等，因此**没有发生任何覆盖**。

### Symbol 属性的访问与遍历 *Content-[04:30]

使用 `Symbol` 作为属性名后，在访问和遍历对象时需要使用特定的语法和方法。

**1. 属性访问**
- **错误方式**：不能使用点语法（`.`），例如 `obj.sym1` 是取不到值的。
- **正确方式**：必须使用中括号（`[]`）语法，例如 `obj[sym1]` 和 `obj[sym2]`。

```javascript
console.log(obj[sym1]); // 输出: 前端必备编程基础
console.log(obj[sym2]); // 输出: 精于前端，专于面试
```

**2. 属性遍历**
- **常规方法失效**：使用 `for...in` 循环或 `Object.keys(obj)` 等常规遍历方法，**无法**遍历到以 `Symbol` 作为 key 的属性。
- **专属遍历方法**：必须使用 `Object.getOwnPropertySymbols(obj)` 方法，才能获取对象中所有以 `Symbol` 作为 key 的数组。

```javascript
// 获取对象中所有的 Symbol 属性名
const symbolKeys = Object.getOwnPropertySymbols(obj);
console.log(symbolKeys); 
// 输出: [Symbol(description), Symbol(description)]

// 遍历并访问 Symbol 属性
symbolKeys.forEach(key => {
  console.log(obj[key]);
});
```

## AI 总结

本节课深入讲解了 `Symbol` 的第一个核心实战场景：**解决对象属性名冲突**。在 ES5 中，对象属性名均为字符串，合并对象时同名属性极易发生覆盖。通过引入 `Symbol` 的唯一性特性，将其作为对象的 Key，可以彻底避免属性覆盖问题，实现属性的完美共存。同时，笔记详细梳理了 `Symbol` 属性的专属访问方式（中括号语法）以及专属遍历方法（`Object.getOwnPropertySymbols`），为应对前端面试和实际企业开发中的对象合并痛点提供了标准解决方案。

---

## 文稿转写

咱们一起再来看symbol的四大实战场景 symbol的所有特性 它最终呢都是为了咱们的开发实战服务的 我在这里呢给大家列举了四个 比较高频次的使用场景 它是也是企业开发当中CBO的核心使用场景 也是面试高频考点 我们来看一下第一个 解决对象属性名冲突的问题 es5中对象名都是字符串 合并对象或者添加属性时 极其容易出现属性名冲突覆盖 而symbol的值它是唯一性 它是唯一的 可以从根本上解决这个问题 那我们先来看es s5的坑点 属性名相同会被覆盖 首先我们来看两个对象 它拥有相同的description属性 咱们来定义一个 第一个对象 O b j e Title 嗯比如说来一个JAVASCRIPT 然后咱们再来一个描述 This is description啊 哪一个前端必备 编程基础好 那我们来看再来一个对象 cons o b勾二 ob Q2呢咱就只有description了 没有title了哈 好精于前端 专于 面试 那接下来的话呢我们要合并两个对象 用什么合并呢 用object a thing in方法 这个方法来合并两个对象 首先空挡 我们要把OB勾一和OB勾二 合并到这个空的对象里 然后返回值 我们用一个OB勾来接一下 好吧 那么下面呢我们来打印一下 在打印之前大家告诉我合并完以后的新对象 ob勾里面它有 首先它是不是得有title字段 title字段呢就是JAVASCRIPT 那么接下来它还会有个description字段 那么describe description字段的值是什么 是精于前端 专于面试还是前端必备编程基础 大家猜一下弹幕给咱走一波是什么呢 我们来看一下啊 好我们来刷新 你可以看到title不用说了 description呢它是精于前端 专于面面试 那也就说明了后添加的也就15行添加的 把咱们第12行的description的值给替换掉了 对不对 这就发生了一个覆盖的问题 是不是 那我们回到课件来看一下啊 那么symbol的解决方案呢 就是用symbol作为属性名来避免冲突 咱们来看 首先呢我们来定义两个symbol值 symbol的变量吧 来一个let 一然后SYMBO 给它一个描述就叫description 再来一个L 2symbol也叫description 描述一样 他俩也是不相等 对不对 那接下来的话呢 我们第一个你就别写字符串description了 应该写成什么呀 应该写成DESCE前端必备编程基础 对不对 那么我们来来看这个 这个的话你也别写字符串了 你就写成DESC2基于前端专于面试 这个时候你再合并两个对象 你看一下保存刷新 你会发现好展开这两个字段是不是都存在呀 他俩看起来长得一模一样 但是他俩其实完全不相等 因为它们是symbol类型 对不对 并没有发生覆盖两 而是两个共存的对吧 那同样的如果你要访问的话 那咱可以这样console点log ob勾 注意访问的时候不能用点 而是中括号 第一个ob勾中括号DSC 第二个我们来看刷新 你看这不都能取到吗 是不是 那么还有如果说你要便利的话 咱们讲了fin呀 这种还有就是object kiss呀 这些方法它是无法便利的 它有自己的便利方法 对不对 比如说它要object点get all property symbol OBO用它才能便利对象中 symbol作为的K值对吧 哎那我们稍加一些注释哈 定义symbol类型 然后下面用symbol类型作为对象的KE 下面的是合并两个对象对吧 剩下的就没必要写了 咱把这个代码放到笔记上 好哦 展这个就没有必要了哈 好覆盖 这个咱没有粘是吧 咱把覆盖的也粘一下啊 好这个代码呢会覆盖 咱已经给他撤销回来了 好OK这就是single的第一个实战场景 也是咱们高频使用的一个场景 就是用symbol解决对象属性名冲突的问题
