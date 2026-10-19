# Symbol 与对象核心交互

## 目录
- Symbol 作为对象属性名的语法要求
- Symbol 属性的三种正确添加方式
- Symbol 属性的错误写法及验证
- Symbol 属性的遍历特性
- 遍历方法对比与 JSON.stringify 处理
- AI 总结

## Symbol 作为对象属性名的语法要求 *Content-[00:00]
`Symbol` 的核心定位之一是解决作为对象 Key 值的唯一性问题，在与对象进行核心交互时，语法要求非常严格：
- **必须使用中括号**：`Symbol` 值作为对象属性名时，必须使用中括号 `[]` 语法。
- **不能使用点语法**：绝对不能使用点语法 `.`。如果使用了点语法，JS 引擎会将其后面的标识符直接解析并当作普通字符串处理。
- **核心原因**：点语法后的标识符会被 JS 引擎解析为字符串，而中括号语法会保留变量的原始类型（即 `Symbol` 类型）。

## Symbol 属性的三种正确添加方式 *Content-[00:45]
在实际开发中，为对象添加 `Symbol` 属性主要有以下三种正确的写法：

1\. **先创建对象，再添加 Symbol 属性**
首先创建一个空对象，然后使用中括号语法动态添加 `Symbol` 键值对。
```javascript
let s = Symbol('JavaScript');
let obj = {};
obj[s] = 'JavaScript';
```

2\. **字面量创建对象时直接添加**
在对象字面量中直接定义 `Symbol` 属性，同样必须使用中括号将 `Symbol` 变量包裹起来。
```javascript
let s = Symbol('ES6');
let obj = {
    [s]: 'ES6'
};
```
*注意：无论是创建时直接添加还是后续动态添加，都必须严格使用中括号。*

3\. **使用 Object.defineProperty 方法**
这是一种更高级的属性定义方式，通过 `Object.defineProperty` 可以精确控制属性的描述符。
```javascript
let s = Symbol('JavaScript symbol');
let obj = {};
Object.defineProperty(obj, s, {
    value: 'JavaScript symbol'
});
```

## Symbol 属性的错误写法及验证 *Content-[03:36]
在使用 `Symbol` 作为属性名时，最常见的错误就是误用点语法。

- **错误示例**：
  ```javascript
  let s = Symbol('JavaScript');
  let obj = {};
  obj.s = 'JavaScript'; // 错误写法
  ```
- **错误原因**：点语法 `obj.s` 会将 `s` 直接处理为普通的字符串键名 `"s"`，而不会将其识别为 `Symbol` 变量。
- **验证方法**：
  1. 尝试通过 `Symbol` 变量访问：`console.log(obj[s])`，结果会返回 `undefined`，因为对象中并没有以该 `Symbol` 为键的属性。
  2. 查看对象结构：打印 `obj` 会发现，对象内部多了一个普通的字符串键名 `"s"`，而不是 `Symbol` 类型的键。
  3. 正确访问对比：如果使用 `obj[s] = 'JavaScript'` 正确添加后，通过 `obj[s]` 就能成功取到值，且对象属性表现为 `Symbol` 类型。

## Symbol 属性的遍历特性 *Content-[05:13]
`Symbol` 类型的对象属性具有“隐藏”特性，不会被常规的遍历方法获取。这一特性在开发中常用于实现对象属性的隐藏，为后续实现私有属性打下基础。

- **无法获取 Symbol 属性的常规方法**：
  - `for...in` 循环：只能遍历到字符串键名（如 `id`, `name`），会忽略 `Symbol` 键。
  - `Object.keys(obj)`：返回对象可枚举的字符串属性名数组，不包含 `Symbol`。
  - `Object.getOwnPropertyNames(obj)`：返回对象所有的字符串属性名（包括不可枚举的），依然不包含 `Symbol`。

- **能够获取 Symbol 属性的专用方法**：
  - `Object.getOwnPropertySymbols(obj)`：专门用于获取对象所有的 `Symbol` 属性名，返回一个数组。注意，它**只**返回 `Symbol` 键，不包含字符串键。
  - `Reflect.ownKeys(obj)`：这是一个“万能方法”，能够同时获取对象所有的字符串键和 `Symbol` 键。

- **获取 Symbol 属性值**：
  通过 `Object.getOwnPropertySymbols(obj)` 获取到 `Symbol` 键的数组后，可以遍历该数组，并通过中括号语法 `obj[sym]` 获取对应的属性值。中括号内的变量名仅作为匹配标识，类似于解构赋值中的变量命名。

## 遍历方法对比与 JSON.stringify 处理 *Content-[10:07]
为了更清晰地理解各种遍历方法对 `Symbol` 和字符串属性的支持情况，可以进行如下对比：

1\. **遍历方法能力对比**
- **仅获取字符串键**：`for...in`、`Object.keys()`、`Object.getOwnPropertyNames()`。
- **仅获取 Symbol 键**：`Object.getOwnPropertySymbols()`。
- **获取所有键（字符串 + Symbol）**：`Reflect.ownKeys()`。

2\. **JSON.stringify 对 Symbol 的处理**
- **现象**：当使用 `JSON.stringify(obj)` 将对象转换为 JSON 字符串时，`Symbol` 类型的属性会被直接忽略。
- **核心原因**：JSON 数据格式规范仅支持字符串、数字、布尔值、数组和普通对象，**不支持 `Symbol` 类型**。因此，在序列化过程中，`Symbol` 键及其对应的值都会被自动过滤掉。

## AI 总结
本视频深入讲解了前端面试与开发中 `Symbol` 与对象交互的核心知识点。重点强调了 `Symbol` 作为对象属性名时**必须使用中括号**的语法规范，并详细演示了三种正确的添加方式及点语法的错误陷阱。此外，视频剖析了 `Symbol` 属性的遍历特性，对比了 `for...in`、`Object.keys`、`Object.getOwnPropertySymbols` 和 `Reflect.ownKeys` 等方法在获取字符串与 `Symbol` 键时的差异，最后指出了 `JSON.stringify` 会因格式限制而忽略 `Symbol` 属性。掌握这些细节对于应对大厂前端面试及实现对象私有属性具有重要意义。

---

## 文稿转写

我们来看与对象核心交互 这就是一个高频使用的一个重点了 开发当中也会涉及到很多 因为它本身的定位呢 就是解决作为对象K值的唯一 那我们来看第一个 symbol作为对象属性名的语法要求 symbol值作为对象属性名时必须使用中括号 不能使用点语法 否则会被当作字符串处理 这个是面试还是开发 你都是能用得到的 它的核心原因就是点语法 后面的标识符会被JS引擎解析为字符串 而中括号它会保留变量的原始类型 那我们来看它有三种正确的写法 首先来看第一种 先创建对象 再添加symbol属性 我们来一个OB勾 等于这是个空的 先创建对象再添加 那就是OB勾 然后比如说S等于来一个JavaScript 这是一种方法 那么还有方法二 你可以打印一下2CONSOL点log o b勾对吧 这个时候打印出来是什么 咱把它拿过来执行一下 刷新OK有个对象 对象里面有一个字段 它是symbol 对不对 就是这个样子的 放到这里 我们再来看第二种字面量 创建对象是直接添加 就我们创建的对象OBJ等于直接添加中括号 S冒号 比如说ES6 这也是可以呀 但是你记着不管你怎么加 创建时候嗯 直接加还是后加 你都得是中括号 对不对 OBJ这个结果呢也是一样的 但是它呢肯定就是呀这个多了啊 然后这点就title这个就没必要了 复制多了 这个结果的话 那不就是es s6嘛 对不对 E s6 然后还有第三种就是用object define property 这种方法比较高级的方法去添加 我们来看 假如说在这里我们定义一个空对象 先来一个 那下来的话呢就是object点define property Define property 第一个参数就是对象对吧 你要给哪个对象OB勾 给它加什么 它的K值是多少 K值值呢 就是s value是多少 给他来个对象value 就让它是哎 不能这么写啊 js JavaScript symbol好吧这样 然后你再来看 也是一样的 OB勾 对不对 是一样的哈 拿过来把这个拿过来 OK呀 这个缩进的太厉害了哈 好 拿过来往这一放 哎这就妥了对吧 三种正确的写法 那么错误的写法呢就是点这个语法 咱们上面也也有提到过 也有给大家详细的讲过 咱们这里呢再强调一下啊 比如说你定义的symbol 就拿它来说吧对吧 错误的语法就是通过点去添加属性 OP勾点S等于JAVASCRIPT 这个时候他会把你的S处理为字符串 并不会把S当做symbol好吗 然后怎么去验证呢 很简单 你就用以symbol的方式 你去访问一下ob 勾好S你能取到吗 取不到的是undefined 看到了吗啊 Undefined 而你看一看你的对象里面怎么加的 这个S是不是就是一个普通字符串呀 如果你添加正确 他这个表现形式不是这样的 你试一下嘛 你把它加上中括号S 你看值是不是取到了 而它呢是不是symbol呀 所以要注意啊 撤回去 咱还是以点的形式保持下来 OK给大家往课件上一放 好结果也写出来 这个呢是undefined 这个呢是对象里面有个S对吧 有个S字符串好 是这样的 OK对吧 这是错误的写法 一定要注意哈 那么还有symbol属性的便利特性 我们来看一下symbol类型的对象属性 它不会被常规便利方法获取 包括fall in for of object keys 还有object get all property names 那么能获取symbol属性的方法有哪些呢 两个get all prompty symbols 还有relax or kiss 这两个是可以的 核心意义呢是实现对象属性的隐藏 为后续实现私有属性打下基础 那我们来看一下这些便利 首先这个我就不啰嗦了 不一便写了 我就拿过来了 往这一放 在这里 我们定义了一个SYMBOS 然后这是一个对象 由id是字符串 name也是字符串 而这个JAVASCRIPT呢它是symbol格式的 对不对 那么接下来我先用第一个 他说不能对吧 For in let一个key印上咱的OB勾 你看按照咱们刚才的理论是最开始说的 fall in是不能遍历symbol的 也就是说它打印出来的key只有id和name 你看什么是果然如此 对吧 好 把这个咱给它剪切到课件上 放到这里 Four in 放映的结果 OK封印的结果再给它放到这里 只有id和name 对不对 那么再来看object keys 好log object点kiss kiss里面直接放成OB勾 按照他说的也不能便利 symbol也就只有id和name 对不对 只不过呢它放到了一个数组里了是吧 好我们把这个也拿过来 放到这里 OK也不能便利symbol 再来看 get all prompty names也不行 Get all prompty names 刷新也不行 也是id和name 没有symbol好拿过来 OK那我们再来试一下专门的方法 能获取symbol的属性 好来第一个get all prompty symbosh Get all prompty symbols 刷新有了没有有了 但是它没有什么呀 没有以字符串作为K值的属性了 它只有SYMBO了 好 OK对吧 这个是可以的 能取到 再来看一个releo kiss 这个也是可以的 OK刷新哦 这里哦我这里写错了哈 保存刷新 你看这个呢不一样的地方 它能去到symbol 没问题 也可以对吧 但是呢他取到的是以字符串和symbol 作为对象 K的都取到了 是不是哎你看这个是不是挺好的呀 全部都能取到 我不管你是啥 我全给你拿过来 写了啊这里获取所有属性字符串和SYMBOT 然后还有这里又写了一个 获取symbol的属性值啊 这个呢写一下嘛 哈咱们知道通过这个get all好 get all from dissymbol是可以取到对吧 那咱就可以把它给干嘛呀 拿到它真正的值 比如说let来一个这个SY等于 让他给到SY对吧 然后你打印一下SYOBJ中括号SY 这个时候就取到了JavaScript哈 这就是取值 还有这里呢我提示大家一下啊 就是中括号这里这个这里呢你叫什么都行好吧 你叫ABC都行 你这里换成ABC就行了好吧 它其实就是个匹配 有点类似于解构赋值好吗 那么我们来看便利方法的对比 fall in能获取字符串吗 能咱就这么说吧 能获取字符串的有哪些 Fall in object keys Get all prompty names 对不对 而能这三个能获取字符串的 反倒是不能获取symbol 对不对 Get all property symbol呢它不能获取字符串 但是它能获取symbol 还有一个万能方法 Reflect or kiss 这个呢是不管字符串还是symbol 它是都能够获取的 我们再来往下看JSONSTRINFI 它呢会忽略symbol属性 如果你使用JSONSTRINFI将对象转为JSON字符串时 cable类型的属性会被直接忽略 为什么呢 核心原用的是JSON格式 仅支持字符串数字布尔数组对象 那它不支持symbol类型 所以就给忽略了 我们来试一个哈 咱就这个吧 就这个就行 来CSOL点log接生 点string five 把ob勾往这一放对吧 那它会转为字符串 转为字符串以后 但是没有JS 因为它是SYMBO的key对吧 刷新你看是不是没有 他就给忽略掉了啊 把这个给他拿过来 复制一下 好嘞
