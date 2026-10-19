# 前端面试：JavaScript 自定义事件 - 移除自定义事件

## 目录
- [核心概念：移除自定义事件](#核心概念移除自定义事件-content-0000)
- [页面布局与元素获取](#页面布局与元素获取-content-0016)
- [自定义事件的核心实现步骤](#自定义事件的核心实现步骤-content-0120)
- [移除自定义事件的实现](#移除自定义事件的实现-content-0346)
- [运行效果与内存管理意义](#运行效果与内存管理意义-content-0439)
- [AI 总结](#ai-总结)

## 核心概念：移除自定义事件 *Content-[00:00]
- **核心要点**：移除自定义事件的核心在于必须使用**具名函数**。
- **注意事项**：如果使用匿名函数绑定事件，则在后续操作中无法被识别和移除。因此，在需要移除事件的场景下，必须将事件处理函数定义为具名函数。

## 页面布局与元素获取 *Content-[00:16]
- **页面布局**：包含两个按钮。
  - 第一个按钮：用于触发自定义事件（`triggerButton`）。
  - 第二个按钮：用于移除自定义事件（`removeButton`）。移除后，再次点击触发按钮将失效，以此证明移除成功。
- **获取元素**：使用 `document.getElementById` 方法获取对应的 DOM 元素。
  ```javascript
  const triggerButton = document.getElementById('trigger');
  const removeButton = document.getElementById('removeButton');
  ```

## 自定义事件的核心实现步骤 *Content-[01:20]
实现自定义事件并触发的完整步骤如下：

1\. **创建自定义事件**
使用 `Event` 构造函数创建一个新的事件对象，并为其命名（此处不传参，直接命名）。
```javascript
const testEvent = new Event('testEvent');
```

2\. **定义具名处理函数**
定义一个具名函数作为事件的处理程序，以便后续能够被精准移除。
```javascript
function customerHandle() {
    alert('自定义事件触发成功了');
}
```

3\. **绑定自定义事件**
将自定义事件绑定到目标元素（`triggerButton`）上，并指定具名处理函数。
```javascript
triggerButton.addEventListener('testEvent', customerHandle);
```

4\. **触发自定义事件**
为 `triggerButton` 绑定 `click` 点击事件，在点击回调中使用 `dispatchEvent` 方法触发自定义的 `testEvent`。
```javascript
triggerButton.addEventListener('click', () => {
    triggerButton.dispatchEvent(testEvent);
});
```

## 移除自定义事件的实现 *Content-[03:46]
- **移除逻辑**：为 `removeButton` 绑定 `click` 点击事件，在回调函数中使用 `removeEventListener` 方法移除之前绑定的自定义事件。
- **关键点**：必须传入与绑定时完全一致的事件名（`testEvent`）和**具名处理函数**（`customerHandle`）。
```javascript
removeButton.addEventListener('click', () => {
    triggerButton.removeEventListener('testEvent', customerHandle);
    alert('自定义事件移除成功了');
});
```

## 运行效果与内存管理意义 *Content-[04:39]
- **运行效果验证**：
  - 初始状态下，点击“触发”按钮，弹窗正常显示，说明事件绑定和触发成功。
  - 点击“移除”按钮后，提示移除成功。
  - 再次点击“触发”按钮，弹窗不再出现，说明自定义事件已被成功移除。
- **内存管理意义**：
  - 及时移除不需要的事件监听器，能够有效**节约内存空间**。
  - 帮助**垃圾回收机制（GC）** 尽早回收相关内存，从而有效**避免内存泄漏**问题。

## AI 总结
本视频详细讲解了前端面试中高频考点“JavaScript 自定义事件的移除”。核心强调了移除事件必须依赖**具名函数**，匿名函数无法被移除。通过完整的代码演示，展示了从创建事件（`new Event`）、定义具名处理函数、绑定事件（`addEventListener`）、触发事件（`dispatchEvent`）到最终移除事件（`removeEventListener`）的全流程。最后指出，及时移除事件监听器对于节约内存、配合垃圾回收机制以及防止内存泄漏具有重要意义，是前端开发中必须掌握的最佳实践。

---

## 文稿转写

再来看最后一个高级版的增加了什么 移除自定义时间 他的重点呢就是移除 自定义事件的核心是具名函数 匿名函数的话无法被识别和移除代码实现一下 咱们来看看 好布局变了 我给他拿过来 那这里的话呢一共俩按钮 第一个按钮呢就是触发自定义事件 第二就是移除 移除了以后再点触发就不能用了 对不对 证明移除成功了 我在这里呢来写一下哈 首先获取需要的元素 Trigger Trigger button document 点get element by id 我老是用这个get element by id去获取元素 那么大家知 不知道有没有别的办法来获取元素了 如果你知道弹幕打一打 敲一敲好吗 Trigger button好吧 然后下面这个呢咱就叫remove button Document get remove button好 接下来就是咱的三部曲 第一步创建自定义实践 对不对 new这个的话呢咱就用英文的就行了 咱又不传参 对不对 咱演示的是移除事件 直接简单点 new event构造函数取个名字 比如说叫test event test event没问题吧 好然后在下面第二步就是定义句名处理函数 不能匿名的 因为匿名函数无法移除 好吧 在这里我们就这个不算算上吧 第二步吧就 Function 比如说取个函数名字 Customer handle好吧 自定义的处理程序 做点事 比如说alert一下自定义事件触发成功了 啊咱就log一下得了 别这个alert了 alert多麻烦 alert alert吧 好吧 alert一下 然后再来看第三步 第三步呢就是绑定 自定义事件绑的时候给谁绑 给这个触发自定时间 也就trigger button对吧 and event listener来一个事件名叫什么test event 对不对 然后触发哪个函数呢 customer handle是不是啊 然后第四步咱就该触发自定义事件 怎么去触发 也是点它trigger button And event listener 来一个点击触发 单击触发 click好 在这里咱用吹trigger button 点上dispatch event 完成事件的触发 事件名就叫test event 对不对 这是可以触发的 我们来刷新看一看 好触发 这不触发了吗 再触发对吧 然后我们现在呢我要加一个移除 就我移除之后不让你触发了 移除自定义事件 移除需要具名函数 咱们已经有了具名函数 点击remove button 点and event listener 点击单击移除哈 我们来一个箭头函数 然后在这里你要移除谁生产的呀 哪个元素 是不是trigger button对吧 用什么移除 Remove listener事件名叫那个移除在哪个呀 test event的 这是咱自定义的事件名对吧 移除的是哪个函数啊 customer handle是不是在这里 我们有个提示 告诉一下用户自定义事件移除成功了好 你再次点击触发自定义事件按钮 它就无效了 试一试刷新好 现在呢是没有移除 点击OK没有问题对吧 再来点击OK没有没有问题 能触发 我们点一下移除自定义事件好 你看自定义事件移除成功了 你再来点触发自定义事件有用吗 没用了 我们来看运行效果 给它写出来运行效果呢就是点击 触发按钮弹窗正常 点击移移除 按钮后再次点击触发按钮无效了 说明移除 自定义事件成功了对吧 这样的话呢能够节约咱们的内存空间 让垃圾回收机制尽可能的早点回收去回收对吧 以避免内存泄漏
