- 1. 伪数组转真数组方法概述
- 2. 方法一：Array.from()
- 3. 方法二：扩展运算符 (...)
- 4. 方法三：Array.prototype.slice.call()
- AI 总结

## 1. 伪数组转真数组方法概述 *Content-[00:00]

- **转换原因**：伪数组本身不能调用真数组的方法（如 `push`、`map`、`filter` 等），在实际开发中通常需要将其转换为真数组后才能进行相关操作。
- **面试要求**：
  - 大厂面试通常要求候选人至少说出 **5 种** 伪数组转真数组的方法。
  - 中小厂面试也至少需要掌握 5 种以上的方法，以体现足够的开发经验。
- **讲解顺序**：以下方法按照**使用频率由高到低**排列。前五种方法最为常用，兼顾了代码的简洁程度与运行性能，建议重点记忆前五种。

## 2. 方法一：Array.from() *Content-[01:46]

- **地位**：ES6 新增的数组方法，**最推荐、开发首选**。
- **特点**：用法简单，兼容性好。
- **基础语法**：`Array.from(likeArray)`

### 示例 1：转换 DOM 元素集合
```javascript
// 获取 5 个 div 元素，返回的是伪数组 (NodeList)
const likeArray = document.querySelectorAll('div');

// 验证是否为真数组，返回 false
console.log(Array.isArray(likeArray)); 

// 使用 Array.from 转换为真数组
const trueArr = Array.from(likeArray);

// 验证转换结果，返回 true
console.log(Array.isArray(trueArr)); 

// 转换后即可调用数组方法，如 map
trueArr.map(item => {
    console.log(item);
});
```

### 示例 2：转换 arguments 并进行数据处理
`Array.from()` 的强大之处在于，它接收**第二个参数**（一个回调函数），可以在转换为真数组的同时，对数据进行进一步处理，实现“一步到位”。

```javascript
function getArgs() {
    // arguments 也是伪数组
    return arguments; 
}

// 传入 5 个参数
const likeArr = getArgs(1, 2, 3, 4, 5);

// 第一个参数为伪数组，第二个参数为箭头函数，将每一项乘以 2
const trueArr = Array.from(likeArr, item => item * 2);

console.log(trueArr); // 输出: [2, 4, 6, 8, 10]，且为真数组
```

## 3. 方法二：扩展运算符 (...) *Content-[07:11]

- **地位**：ES6 新增语法，**最简洁**，开发中也非常常用。
- **基础语法**：`[...likeArray]`

### 基础示例
```javascript
const likeArray = document.querySelectorAll('div');

// 使用扩展运算符转为真数组
const trueArr = [...likeArray];

console.log(Array.isArray(trueArr)); // 返回 true

// 可正常调用数组方法
trueArr.filter(item => {
    console.log(item);
});
```

### ⚠️ 避坑点（大厂面试必考）
扩展运算符**仅能转换实现了 `Iterator` 接口的伪数组**（即可被 `for...of` 循环遍历的对象，如 `arguments`、`NodeList` 等）。

**错误示例：自定义伪数组**
如果自定义一个伪数组（仅有 `length` 属性和索引，未实现 `Iterator` 接口），使用扩展运算符会报错。
```javascript
const likeArray = {
    0: 'a',
    1: 'b',
    length: 2
};

// 报错：TypeError: likeArray is not iterable
const trueArr = [...likeArray]; 
```
**结论**：不能被遍历（未实现 `Iterator` 接口）的伪数组，不能使用扩展运算符转换。

## 4. 方法三：Array.prototype.slice.call() *Content-[10:43]

- **地位**：ES5 中的经典方法，**面试常考底层原理**。
- **基础语法**：
  - 标准写法：`Array.prototype.slice.call(likeArray)`
  - 简写形式：`[].slice.call(likeArray)`（前提是没有重写 `slice` 方法）

### 基础示例
```javascript
const likeArray = document.querySelectorAll('div');

// 使用 slice 和 call 转换
const trueArr = Array.prototype.slice.call(likeArray);
// 或者简写
// const trueArr = [].slice.call(likeArray);

console.log(Array.isArray(trueArr)); // 返回 true
```

### 底层原理（大厂面试深度解析）
- `slice` 方法内部是通过**索引遍历**来获取元素并返回新数组的。
- 只要一个对象拥有 `length` 属性和数字索引，就可以被 `slice` 方法遍历。
- 通过 `call` 方法，将 `slice` 内部的 `this` 指向伪数组，从而成功将其转化为真数组。

## AI 总结

本视频详细讲解了前端面试中高频考点“伪数组转真数组”的三种核心方法：
1. **`Array.from()`**：ES6 方法，开发首选。不仅用法简单，还支持传入第二个回调函数，在转换的同时完成数据映射处理，功能最强大。
2. **扩展运算符 `...`**：ES6 语法，代码最简洁。但需特别注意，它**仅支持实现了 `Iterator` 接口的伪数组**，对于自定义的无迭代器接口的伪数组会抛出类型错误。
3. **`Array.prototype.slice.call()`**：ES5 经典方案。通过 `call` 改变 `this` 指向，利用 `slice` 内部基于索引遍历的特性实现转换，是理解 JavaScript 底层原型和 `this` 指向的绝佳案例。

在面试中，建议至少熟练掌握前 5 种方法，并能清晰阐述扩展运算符的 `Iterator` 接口限制以及 `slice.call` 的底层原理，以展现扎实的前端基础。

---

## 文稿转写

咱们再来看伪数组转真数组的方法 我们知道伪数组本身是不能调用数组方法的 对不对 开发中需要转为真数组后才能调用 比如说push map等数组上的 方法我们将介绍七种 下面介绍七种伪数组转 真数组的方法 而且呢大厂面试要求你至少说出五种 说出五种 哪怕是小厂中场面试人问你 你知道哪些伪数组转成数组的方法 那咱最起码得能说出五种以上吧 你说个一种两种 那你这3年开发经验 5年开发经验对吧 是不是不太合适呀 我们下面讲的时候会按照 使用频率由高到低讲解排列 大家记的时候啊 你就记前五种就行 既然使用频率也是由高到低的 使用频率高的 那必然是好用的 对不对 不管是它的简洁程度还是性能方面都考虑到了 是不是啊 大家最起码记住前五种好 我们来看第一种 Array from 这是最推荐的开发首选 它呢是es6新增的数组方法 专门用于将伪数组转为帧数组 用法简单 兼容性好 开发首选 我们来看它的语法也很简单 ARA点from它的参数呢你可以放上伪数组 这就可以了 我们来写个例子 让大家感受一下它的强大功能 在这里我们来创建五个div 这是一个伪数组 Document 点query Selector All 好把div放进来 我们知道这个呢通过query selector of 获取到的元素 它是尾速度 对不对 你可以再来测一下吗 用什么测array 点is array 看它是不是一个正数组排 它必然会返回false对吧 那么接下来的话呢我们给它转为真数组 使用咱的reform 接一下吧 Const true array Array 点from like array 这个时候你再打印一下true arr 它必然是true了 我都不用打印 我都知道哼 我怎么知道的哎 so咱写的是true 结果呢在没加什么 没加arr d i is array好 你从这个其实也能看出来他是个数组 对不对 如果他是伪数组的话 他不是这个样子的是吧 好来一个true哈 我还特别自信的结果还说的不太准确哈 那么既然是正数组了 那就可以调数组的方法了 比如说触点map 别的不干 咱就把每一个div打印出来就行了 CONSOL点log item保存刷新 OK吧好 那么它的优势是什么呢 它的优势就是还能 就是在你转为 增数组的同时 还可以 处理进一步处理数据啊 一步到位了 就进一步处理数据 或写针对帧数组的逻辑处理 好我们来举个例子给大家看一下啊 这个呢咱举的是这个获取元素 我们再来一个arguments词 这个咱就不要了 比如说咱们来定义一个方法 Function get 好return Arguments 调用这个方法传入12345 好 插入五个参数 然后接一下 好了 那么这个时候我们知道它是个什么呀 尾数组对不对 你再来验证一下嘛 array点is array 对不对 A22刷新 因为我们讲了arguments 它也是伪数组 那我们再来看一下 如果说我们在转为尾数 转为正数组以后 这个留着哈 转为正数组以后 我们还要让它呢乘以乘以个二 也就是变成它的两倍数 对不对 我们可以这样去做array点from第一个参呢 它是你的尾数组 还可以有第二个参好 直接来个箭头函数 让每一项乘以个二 然后返回值就是你处理之后的一个新的整数组 那我们来看一下 好处array 那结果是多少呀 首先它的结果一定是个真的数组 对不对 然后这个没用了啊 然后数组里面的每个元素 是不是都乘以了一次二呀 1×222得42468十 对不对 好刷新是这意思吧 你看对吧 我不光把你转为了帧数组 我还对你做了其他的逻辑处理 一步到位 就这意思好吗 再来看第二种ESU的扩展运算符三个点 这是最简洁 开发呢也比较常用 它的语法特简单 来一个数组点点点 然后放上你的伪数组就可以了 我们来举个例子好 还是这个例子哈 这个获取到的是伪数组 咱们这个测试咱就不要了啊 大家已经知道了 少点代码说的更清楚更清晰 然后转为真数组 咱不用ARREFORM了 咱换一下用什么呢 用扩展运算符const true array等于数组三个点 然后like array 我们来看一下 验证一下 先它是不是一个真的数组 array点a n array true a r r返回true 那就是真数组 对不对 返回true了 说明他是一个真的数组 真的数组 那咱就可以调用数组上的方法 比如说filter来个过滤对吧 过滤咱不做逻辑处理 把它打印出来就行 CONSOL点log item保存 刷新5div取出来了对吧 这就是可以正常调用数组方法 是不是这个结果啊 是一个true true 就代表帧数组把写完的代码记忆时拿过来 OK那我们来往下看 这里有一个避坑点 大厂面试必考扩展运算符仅能转换 实现了INTEGROR接口的伪数组 什么是inter reor呢 就是可被循环遍历的 比如说到我们集合arguments file list 你自定义的无形特瑞特接口的尾数 都是无法使用扩展运算符来转换的 我们来试一个自定义的尾数组 这个咱不要了 跟他没关系 我们来自定义一个伪数组 like array等于 0112 你要是看的乱 我给你来字符串吧 A好吧 好B它不能少什么length Length 给它个二好得了 这就是咱自定义的 尾数组 那我们要转自定义尾数组 你看下面这些就别了 这个咱不要了啊 保存刷新有没有报错 报了报什么错 类型错误 Like array is not interacable 它不能被便利 所以呢不能被便利的 你就不能用三个点扩展运算符转为真数组 一定要注意好吗 把错误给大家拿过来 在第15行 这个没用了啊 压根儿报错了 还用测吗 不用测了 肯定转不了嘛 都已经报错了对吧 OK那我们再来看第三种方法转为数组的 这是es5的经典面试常考底层 我们来看它的作用 它利用的是 数组的 Slice 方法这个方法呢它会返回新数组 通过call改变this指向伪数组实现转换 它是 es5中的es5中最经典的转尾数组的方法 它的语法稍微长一些啊 而锐点proto type点slice 点co 这里放上你的尾数组 你也可以简写或简写为这样来个数组点slice 点co为数组也行啊 正常情况下你用简写就行 只要你自己没有把这个slice方法给重写 就没有问题 可以用简写好吧 如果你重写了 那你需要用数组原型对象上面的slice好吧 那我们来试一个哈 撤销回去 来一个伪数组 然后我们转为真数组 用array接一下 array点proto type 点slice 点co参数就是你的尾数组 我们来看一下 能不能转成功保存刷新 看看着就是个数组 对不对 有必要测吗 测想测就测一下呗 返回true不就对了吗 对吧 这就转成功了啊 OK那么你还可以简写 简写也没有问题啊 那咱这里就简写吧 直接改啊 留着吧 就就这样简写 大家好好听哈 刷新是不是也没问题啊 OK咱把代码拿过来 大厂咱们讲的大厂会问底层原理 那这个底层原理是什么呢 就是slice方法呀 内部是通过索引便利获取数组 获取元素的 获取元素并 返回新数组 只有对象有length和索引 就被就可以被 slice锁便利 因此通过扣将this指向为指向到伪数组后 就能实现转化为生数组了 这就是它的原理
