## 目录
- 引言：定位乱飞的根本原因
- 什么是 Containing Block
- position: relative 的包含块规则
- position: absolute 的包含块规则
- position: fixed 的包含块规则与例外
- 百分比尺寸与 Containing Block 的关系
- 课程核心总结
- AI 总结

## 引言：定位乱飞的根本原因 *Content-[00:00]

在日常前端开发中，经常会遇到“定位乱飞”的问题。例如，想将一个按钮放在卡片的右上角，给子元素设置了 `position: absolute`，并设定 `top: 12px` 和 `right: 12px`。但刷新页面后，按钮要么跑到了页面整体的右上角，要么出现在完全意想不到的位置。

面对这种情况，很多开发者会开始“试探性修改”：
- 给父元素加一个 `position: relative`。
- 如果不行，就给祖父元素也加上。
- 甚至开始盲目修改 `top` 的值（如 0, 12, 24 等）。

这种“试错”过程让人觉得 CSS 很玄学。但实际上，**CSS 一点都不玄学**。定位乱飞的根本原因在于开发者脑海中默认了一个错误的规则：“`top` 和 `left` 是相对父元素计算的”。

浏览器真正遵循的规则是：**所有定位的偏移、百分比以及尺寸的计算，都是相对于 Containing Block（包含块）进行的**。理解并掌握 Containing Block 的判定规则，是解决定位问题和应对相关面试题的关键。

## 什么是 Containing Block *Content-[01:51]

**Containing Block（包含块）** 的定义非常直观：它是浏览器在计算一个元素位置或者尺寸时，用作参照的那个**矩形框**。

需要特别注意的是：
- 它是一个“参照矩形”，而**不是某个具体的 HTML 标签**。
- 当浏览器计算样式时（例如 `top: 20px` 或 `width: 50%`），它需要知道这个数值是“相对谁”计算的，这个“谁”就是 Containing Block。

**思维转变**：
以后遇到定位乱飞的问题，不要第一时间去改 `top` 或乱加 `relative`，而是要问自己一个核心问题：**“这个元素的 Containing Block 是谁？”** 当你能在面试中准确说出这句话时，就能向面试官证明：你解决定位问题的方式已经从“试出来”升级为了“算出来”。

本节课主要围绕 `position` 属性的四个常见值（`static`、`relative`、`absolute`、`fixed`）来讲解 Containing Block 的判定规则。

## position: relative 的包含块规则 *Content-[03:22]

`position: relative` 的核心特性是**相对自己原位置偏移，且不脱离文档流**。

**代码示例与验证**：
1. 构建一个父容器 `line`，内部包含三个子 `div`（A、B、C），正常排布为一行。
2. 给 `box B` 添加 `position: relative`，并设置 `top` 和 `left` 的偏移值。
3. 刷新页面后，B 发生了偏移，但 A 和 C 的位置**并没有**因为 B 的偏移而重新排版。

**结论**：
- `relative` 并不是重新定位，它只是先按文档流站位，之后再做视觉上的偏移。
- **Containing Block 规则**：`relative` 的偏移参照点，是**它自己原本在文档流中的位置**。
- **面试加分项**：如果面试官追问“`relative` 会不会脱离文档流？”，应明确回答“不会”。它仍然占据原来的空间，旁边的元素也不会补上它挪走后的空间。

## position: absolute 的包含块规则 *Content-[04:50]

`position: absolute` 会脱离文档流，其 Containing Block 的判定规则是：**向上查找最近的非 static 定位祖先元素（即最近的已定位祖先）**。

**代码示例与验证**：
1. 构建层层嵌套的 HTML 结构：`section > grand > parent > child`。
2. 给最内层的 `child` 设置 `position: absolute` 以及 `top` 和 `right` 偏移。
3. **场景一**：`grand` 设置 `position: relative`，`parent` 保持默认 `static`。此时 `child` 会贴在 `grand` 的右上角，因为它的 Containing Block 是 `grand`。
4. **场景二**：删除 `grand` 的 `relative`，改给 `parent` 加上 `position: relative`。刷新后，`child` 会贴在 `parent` 的右上角。这就是 Containing Block 查找规则的肉眼验证。

**结论与面试话术**：
- `absolute` 的坐标原点**不是父元素**，而是**最近的非 static 元素**。
- **面试官追问**：“为什么大家喜欢在父元素上写 `relative`？”
- **高分回答**：因为很多时候父元素就是我们期望的 Containing Block，我们就是想让子元素 `absolute` 的参照物固定在父元素上。这展现了底层认知，而非死记硬背口诀。

## position: fixed 的包含块规则与例外 *Content-[06:47]

关于 `position: fixed`，大家通常的认知是：“相对 `VIEWPORT`（视口）定位，页面滚动时元素不会动”。这句话在常规情况下是正确的，但**不够完整**。面试官一旦问到例外情况，很多人就会卡住。

**常规情况**：
将 `child` 设置为 `fixed`，它会直接相对于浏览器 `VIEWPORT` 的右上角定位，而不是相对于 `grand` 或 `parent`。

**例外情况（高频考点）**：
1. 给祖先元素 `grand` 添加 `transform` 属性（如 `transform: translateX(0)`）。
2. 刷新页面后会发现，`child` 不再贴着 `VIEWPORT` 的右上角，而是**被 `grand` “吸住”了**。

**核心结论**：
- 当祖先元素通过特定的 CSS 属性**创建了新的 Containing Block** 时，`fixed` 元素的参照系就会从 `VIEWPORT` 变成这个祖先元素。
- **能创建新 Containing Block 的属性包括**：`transform`、`filter`、`perspective` 或 `will-change`。
- **底层原理**：浏览器为了渲染**合成层（Composite Layer）**，合成层会建立新的坐标系统（关于合成层的概念会在后续课程详细讲解）。
- **面试杀手锏**：“祖先元素可以通过 CSS 属性改变 `fixed` 元素的参照物”，记住这句话，能在面试中与绝大多数候选人拉开差距。

## 百分比尺寸与 Containing Block 的关系 *Content-[08:25]

除了定位偏移，**百分比尺寸的计算同样依赖于 Containing Block**。这是一个容易被忽略的细节。

**示例说明**：
- 当 `child` 为 `fixed`（且 `grand` 有 `transform`）时，设置 `width: 50%`，其宽度是相对于 `grand` 宽度的 50%。
- 当 `child` 改回 `absolute`（且 `parent` 为 `relative`）时，设置 `width: 50%`，其宽度变成了相对于 `parent` 宽度的 50%。

**本质总结**：
所有的定位偏移加上百分比的尺寸，本质上都是在问同一个问题：**这个元素的 Containing Block 是谁？** 或者说，所有的 CSS 定位与布局问题，最终都可以归结为 **Containing Block 的判定问题**。在面试中点出这句话，是证明你真正理解该知识点的核心话术。

## 课程核心总结 *Content-[09:18]

用三句话总结本节课的核心内容：

1\. **CSS 不是玄学**：定位乱飞不是因为 CSS 玄学，而是因为我们的参照系（Containing Block）没有找对。
2\. **absolute 的核心逻辑**：`absolute` 的关键不仅仅是脱离文档流，更重要的是向上找到最近的定位祖先作为 Containing Block。
3\. **fixed 的参照系陷阱**：`fixed` 通常相对于 `VIEWPORT`，但如果祖先元素创建了新的 Containing Block（如使用了 `transform` 等属性），其参照系也可能会发生改变。

**实战建议**：
以后在面试或开发中遇到定位问题，不要盲目去改 `top` 或 `left`，而是要先问自己：**“这个元素的坐标原点是谁？Containing Block 到底是谁？”** 能把这个逻辑讲清楚，将是非常大的加分项。

## AI 总结

本节课程深入剖析了前端 CSS 布局中极易导致“定位乱飞”的核心概念——**Containing Block（包含块）**。视频打破了“定位相对父元素”的常见误区，明确指出所有定位偏移与百分比尺寸的计算均依赖于 Containing Block。课程详细推导了 `position` 属性下 `relative`、`absolute` 和 `fixed` 的包含块判定规则，并重点强调了 `fixed` 定位在祖先元素存在 `transform` 等属性时会发生参照系转移的进阶考点。掌握 Containing Block 的判定逻辑，能够帮助开发者从“盲目试错”转变为“精准计算”，是提升 CSS 底层认知和应对大厂前端面试的关键。

---

## 文稿转写

好同学们大家好 欢迎回到我们的前端高频面试题系列课程 这节课程 我们继续围绕HTML与CSSS的高频面试知识 进行讲解 这节课程我们讲解的是containing block 也就是元素的坐标原点 在视频开始之前 我们已经将视频配套资料和大厂面试题 整理整理好 老规矩 三连留言 我们开始学习好 我们开始今天的课程 这节课程很可能是我们在前端开发过程中 经常遇到的一个定位乱飞问题 第一次我们将来把它给大家理解清楚 好 我们首先从一个大家一定遇到过的场景开始 我们写了一个按钮 想把它放在卡片右上角 我们写子元素absolute 然后top给了一个12的pixels 然后right给了一个12pixels 之后我们刷新页面按钮 要么跑到了页面右上角 要么跑到一个我们完全想不到的位置 我们这时候开始做什么 我们开始试探性的修改 比如给负元素加一个position relative 再不行就给组副元素也加 再不行就把top改成零十二二十四 我们一边改一边怀疑人生 CSS为什么这么玄学 今天要告诉大家的是 CSS一点都不玄学 我们之所以觉得玄学 是因为我们脑子里一直默认一句话叫做top left 相对负元素 这句话从来都不准确 浏览器真正遵循的是另一句话 也就是我们高亮出来的所有定位的偏移百分比 尺寸的计算都是相对于containing block啊 那这节课我们就做了一件事 就是把containing block变成大家脑子里一个能推导 能解释 能在面试过程中表达的规则系统好 首先什么是contenting block 我用一句大家都能听懂的话来定义它 Containing block 是浏览器在计算一个元素位置或者尺寸时 用作参照的那个矩形框 要注意它是参照矩形 它并不是某个标签 我们可以把它这样理解 在浏览器算账的时候会问一个问题 比如我们给了一个top20像素 那这个20是相对谁的 我们给了一个宽度是50% 那这个50%又是相对谁的 那这个谁就是containing block 所以我们以后遇到定位乱飞的问题 不需要第一时间改top 也不需要乱加reality 我们关键是要问自己一个问题 叫做这个元素的containing block是谁 当我们能在面试中说出这句话的时候 面试官就知道我们在解决定位问题的时候 我们的方式从试出来变成了算出来好 那今天这节课我们主要讲四类containing block 相关的这个CSS属性分别是position的四个值 Static relative Absolute fix 这也是我们在面试过程中和开发过程中 最常遇到的四个情况 好static呢就是默认文档流 而relative是相对自己原位置偏移 absolute是脱离文档流 而fixed通常相对VIEWPORT 我们先把这四个结论给出来 然后我们再带大家用一个真实的例子去理解好 我们现在依然写几个 在HTML里写一些元素来演示这个例子好 我们先写三个box 分别是ABC 我们把他们三个div标签放到一个芙容器中 这个副容器我们暂时先叫做line 给他一个class name 好在HTML完成之后 我们贴一些我们已经写好的样式进去 然后我们刷新页面就会发现 页面上这个时候有ABC3个盒子 正常排成了一行好 这样看上去很正常 接下来我们给box b加一个position relative的CSS属性 以及对应的偏移 给一个top和给一个left 好我们接下来我们再刷新一下这个页面 我们会发现B往右下进行了偏移 但A和C的位置 并没有因为B的偏移而重新排版 这说明什么 说明relative并不是重新定位 它只是先按文档流站位之后再做视觉上的偏移 所以relative的containing block我们可以这样说 relative的偏移参照点 是他自己原本在文档流中的位置 也就是我们这里提到的自己原来的位置好 如果面试官追问说 relative会不会脱离文档流 我们可以明确的告诉他 不会 他仍然占位置 是视觉上的偏移 所以旁边的元素也不会补上 它挪走之后的空间好 接下来我们来看absolute 首先我们给出我们的结论叫absolute 会向上查找最近的定位祖先 也就是position 不是static的祖先元素依然通过code 我们来理解这句话好 首先我们把这个HTML结构里 在先加一部分section进去 我们先加一个stage 在内部嵌套三层子的div的元素 一个grand 一个parent好 再加一个children好 再一个child OK好 现在我们这段HTML的section已经构建完成了 它是一个层层嵌套的结构 接下来我们继续去写一写这个CSS样式好 我们好 我们刷新页面之后就发现这个child的标签 它贴在了grand的右上角 这是为什么 因为它有一个position absolute的属性 它会向上找到定位的祖先 而parent呢他没有写position 所以它是默认的static的一个值 grand写了position relative 所以child的containing block就是grand好 所以它也相对于grand去做这个定位 所以他也就贴在了grand的右上角 那接下来我们来做一个改动 我们把GRANDE的position relative删掉 然后给parent来加上好 我们就会看到刷新之后 child贴在了parent的右上角 这就是containing block查找规则的肉眼验证 所以我们就可以得出一个结论 叫做absolute的坐标 原点不是负元素 而是最近的非static元素 也就是最近的已定位祖先 那面试官可能会追问说 为什么大家喜欢在负元素上写relative 那这个时候我们就可以回答 因为很多时候负元素就是我们希望的 Containing block 我们就是想让子元素 absolute的参照物固定在负元素上 这就是我们的展现出来了我们的底层认知 而不是我们的记忆口诀好 接下来我们来看最后一个属性叫fixed 然后fixed大家的认知通常大家都会背一句话 叫做fixed 相对VIEWPORT滚动的时候 这个元素它也不会动 这句话不能算错误 但它也不够完整 面试官一旦会问到例外的时候 很多人就会卡住了 我们基于刚才的结构 把child的position改成fixed 同时我们也稍微改一下这个top和right的值 而我们刷新页面 就会看到child跑到了浏览器右上角 而不是grand或者parent的角落 这也就是大家熟悉的fixed 但这个时候我们要创制造一个变质的条件 我们现在给一个祖先元素 给这个grand加上一个transform的属性 好我们刷新一下页面 这个时候我们会看到一个现象叫child 它不再贴着VIEWPORT的右上角 而是出现在被grand吸住了的效果 这就是为什么我们要强调这个结论 当祖先元素创造了新的containing block 例如transform属性的时候 fix的元素的参照系就会从VIEWPORT变成这个祖先 大家记住这句话 这将是我们面试中和其他候选人拉开差距 非常重要的一个结论 叫做祖先元素可以通过CSS属性 改变fixed元素的参照物 这些属性包括我们刚才用的transform 也包括像filter perspective或者will change 为什么会创造新的containing block 因为浏览器为了渲染合成层 合成层会建立新的坐标系统 关于合成层的概念 我们在后续的课程中会进行更加详细的讲解 大家现在只需要记住这个结论就可以了 接下来我再补一个大家很容易忽略的点 我们经常给一个百分比的宽度 那这种百分比其实也是看continue block 比如我们child给了一个50% 现在就会相对它的grand的元素 是一个它的50%的宽度 那我们现在再把child改回app solute 我们再来看一下这个结果 我们就发现它的50%的宽度 变成了parent的宽度的50% 因为这个时候他的containing block就是parent 所以说我们所有的定位偏移加上百分比的尺寸 本质都是在问同一个问题 就是这个元素的containing block是谁 或者说所有的定位问题都是在问同样一个问题 叫做containing block的判定问题 记住这句话 这将是我们在面试中告诉面试官 我们真正理解了这一点的关键 关键的总结或者说关键的话术 接下来我们用三句话来总结今天的课程 第一句话叫做CSS 它不是玄学乱飞 是因为我们的参照系没有找对 第二句话是absolute的 关键也不是脱离文档流 而是向上找到最近的定位 祖先作为containing block 第三句话 fixed通常相对于VIEWPORT 但如果祖先创建了新的containing block 参照系也可能会改变 所以以后不管是在面试中还是在开发中 遇到这类问题 我们要不要先改top或者left 然要先问自己这个元素的坐标原点是谁 containing block到底是谁 我们在面试中如果能把这句话讲清楚 将会非常突出 好今天的课程就到这里 谢谢大家
