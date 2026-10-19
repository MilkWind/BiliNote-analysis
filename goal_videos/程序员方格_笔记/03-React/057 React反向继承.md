## 目录

- 什么是反向继承
- 反向继承的适用场景与注意事项
- 反向继承的核心特性与代码示例
- 属性代理与反向继承的对比
- AI 总结

## 什么是反向继承 *Content-[00:00]

在 React 中，高阶组件（HOC）的实现方式主要有两种：属性代理（Props Proxy）和反向继承（Inheritance Inversion）。

1\. **常规继承**：
常规情况下，组件的继承方式是直接继承自 `React.Component`。
例如：`class MyComponent extends React.Component`。

2\. **反向继承**：
反向继承是借助一个函数，接收一个组件（WrappedComponent）作为入参，返回一个新的组件（EnhancedComponent）。
其核心在于，新组件继承自**传入的组件**，而不是 `React.Component`。
例如：`class EnhancedComponent extends WrappedComponent`。

**为什么叫“反向”？**
在常规继承中，基类（Base Class）是 `React.Component`；而在反向继承中，传入的 `WrappedComponent` 被当做了基类。继承的方向发生了反转，因此被称为反向继承。

## 反向继承的适用场景与注意事项 *Content-[02:07]

### 适用场景
反向继承仅在**需要深度控制组件内部逻辑**时使用。由于它是通过继承实现的，其权限比属性代理（Props Proxy）更高。

### 核心能力
- 劫持、截取对应的生命周期方法。
- 修改渲染的结果（Render Tree）。
- 强制更新策略。

### 注意事项与建议
由于反向继承的权限非常高，容易破坏组件的封装性，因此需要谨慎使用：
- **避免滥用**：优先考虑更加安全的属性代理方式或 React Hooks 来处理相关逻辑。
- **保持最小侵入性**：尽量通过 `super` 调用保留的原始组件行为（如调用父类的方法），保持组件行为的继承性。
- **按需覆盖**：仅在必要的时候去进行方法覆盖。
- **避免直接修改**：尽量避免直接修改原始组件的 `state` 和 `props`，除非有明确的要求。

## 反向继承的核心特性与代码示例 *Content-[04:23]

反向继承允许在 HOC 中通过 `this` 访问被包裹组件的相关属性，并直接读取和操作 `state`、`props` 以及渲染结果。

### 1. 劫持生命周期
可以在增强组件的生命周期中，先调用父类的生命周期，再执行增强逻辑。
```javascript
componentDidMount() {
  // 检查父类是否存在该生命周期方法
  if (super.componentDidMount) {
    super.componentDidMount(); // 执行父类生命周期
  }
  // 执行增强逻辑...
}
```

### 2. 修改渲染结果 (Render)
通过 `super.render()` 获取原始组件的渲染输出，并在其基础上进行修改或包裹。
```javascript
render() {
  const originRender = super.render(); // 拿到原始渲染结果
  // 在渲染结果之前包裹一层元素
  return <div className="wrapper">{originRender}</div>; 
}
```

### 3. 读取与操作 State
可以直接读取和操作被包裹组件的 `state`（但不建议直接修改）。
```javascript
// 读取并增强 state
this.state = { ...this.state, enhanced: true };
```

### 4. 条件渲染
在 `render` 方法中，可以根据传入的 `props` 进行条件判断，决定渲染逻辑。
```javascript
render() {
  if (this.props.isVisible) {
    return super.render(); // 调用父组件渲染
  }
  return <div>Component is hidden</div>; // 自定义逻辑
}
```

### 5. 修改子元素 (React.Children / cloneElement)
可以遍历并克隆子元素，统一注入额外的属性或元素（如添加红色边框）。
```javascript
render() {
  const originRender = super.render();
  // 遍历并克隆 children
  const newChildren = React.Children.map(originRender.props.children, child => {
    return React.cloneElement(child, { style: { border: '1px solid red' } });
  });
  return React.cloneElement(originRender, null, newChildren);
}
```

### 6. 修改特定元素的 Props
可以深入渲染树，修改特定类型元素的属性。例如，为所有的 `input` 元素添加默认的 `placeholder`。
```javascript
render() {
  const tree = super.render();
  const newTree = React.Children.map(tree, element => {
    if (element.type === 'input') {
      // 修改 input 的 props
      return React.cloneElement(element, { placeholder: 'Please input...' });
    }
    return element;
  });
  return newTree;
}
```

### 7. 处理 Ref 转发
可以通过 `React.forwardRef` 处理 ref 转发，将 ref 正确绑定到被包裹的组件上。

## 属性代理与反向继承的对比 *Content-[13:08]

属性代理和反向继承都属于高阶组件（HOC）的实现模式，它们既有相同点，也有显著的区别。

### 相同点（HOC 的本质）
两者的本质都是：**接收一个组件作为入参，返回一个新的组件**。无论是属性代理还是反向继承，都符合这一定义。

### 属性代理 (Props Proxy)
- **实现方式**：基于**组合**（Composition）的方式增强组件。
- **操作视角**：从外部进行操作，不会对 `WrappedComponent` 本身做修改。
- **功能范围**：主要对当前的 `props` 进行增、删、改操作。
- **权限与安全性**：权限相对较低，无法直接访问组件内部的 `state` 和生命周期，因此**更加安全**。

### 反向继承 (Inheritance Inversion)
- **实现方式**：基于**继承**（Inheritance）的方式增强组件。
- **操作视角**：从内部进行操作，通过 `super` 关键字可以访问原来组件的内部逻辑。
- **功能范围**：可以操作生命周期、读取/修改 `state`、拿到 `render` 后的 Tree 并修改渲染内容。
- **权限与安全性**：权限非常高，功能极其强大，但如果不加节制地使用，容易带来副作用，需要开发者自行约束。

## AI 总结

本视频详细讲解了 React 高阶组件（HOC）中的**反向继承（Inheritance Inversion）** 模式。与常规的属性代理不同，反向继承通过让新组件继承传入的 `WrappedComponent`，实现了对组件内部逻辑的深度控制。其核心优势在于极高的权限，允许开发者劫持生命周期、修改 `state` 和 `props`、以及深度修改渲染树（Render Tree）。然而，正因为其强大的破坏力，视频强烈建议开发者保持最小侵入性，优先使用更安全的属性代理或 Hooks，仅在必须深度干预组件内部行为时才谨慎使用反向继承，并务必通过 `super` 保留原始组件的基础行为。

---

## 文稿转写

版权继承呢它主要是通过哦 呃可能同很多同学没有用过对应的反向继承啊 我们就可以它是借助一个函数 它接收一个组件作为对应的一个入参 同样是接收都是接收我们的组件 作为我们当前啊作为一个参数 返回我们新的组件 只不过我们这样新的组件 它是继承自我们传入的组件 为什么叫反向继承对吧 所以同学们一定要清楚什么叫反向继承 为什么叫反向继承 同学们一定要清楚啊 那么一我们呃常规情况下 常规信息发 我们的继承方式是通过比如说my component Intense 我们react component对吧 这是我们常规情况下的一个继承 那么而在反向继承当中呢 反向继承当中呢 我们是怎样的一个继承 这是我们的常规继承 反向继承中呢 我们就可以通过 它会继承了我们传入的组件 他继承的是我们warmer的component 那么warm Comp呢就是我们的入餐对吧 所以说这是我们的这样一个反向继承 所以整体来看就是反向的 本来是我们需要继承的 是我们red component的结果 我们呃继承的是我们传入的组件 那么所以说我们WEBCOMMENT那被当做了鸡肋 这就是我们的看出我们的base class base class好 所以说我这是我们反应性 那么我们哪些适用场景呢 我们有哪些适用场景呢 我们仅在 仅在我们需要深度控制我们组件的时候 组件内部逻逻辑的时候需要使用他的权限 是比我们刚之前首先代理他的权限更高的 因为我们可以去劫持截取对应的生命周期方法 我们可以去修改渲染的结果 我们可以去强制更新策略 所以说它是权限是非常高的 那么我们应该避免去滥用 避免有滥用我们当前的呃整个这样一个方式啊 我们优先考虑更加安全的一个方式 更加安全属性代理 也就是比如说我们属性代理的方式 或者我们hook的方式来去呃 做相关的一些逻辑 我们应该额减少 我们其实减少我们当前反向代理 继承的一个使用啊 因为它的权限确实太高了 好 我们就尽量保尽量保持我们最小的一个侵略性 侵入性 保持进行最小的一个侵入性 我们应该尽量通过super 尽量通过super 然后去调用我们保留的原始的组件的行为 比如调用父类的方法 保持我们组建行为的一个句型 仅在我们必要的时候去进行覆盖方法 所以说我们建议给同学们是这样的一个建议啊 以及我们避免去直接修改原始组件的state呀 还有purpose啊 这都是我们尽量去避免的 除非有明确的一个要求 所以这都是哦从同学们一定要格外去注意啊 那么我们看看这样嗯 我们看看一个简简单例子 我们看这个应该这个也简单 例子我们传入了对应的barber component 对吧 我们最终是extends 我们rap component 所以说这就是我们反向 我们这样一个反向继承的一个思路 那么我们在我们当前的enhance 其实也是有有对应的component DEMT这样的生命周期呀对吧 那么这个生命周期呢 我们其实是可以去劫持我们哦 哦鸡肋的这个组件的一个生命 这父类的组件的生命周期 那么我们看看我们当前super哦 可不能demount是否存在 如果存在的话 我们就执行一下啊 我们父类的生命周期 那么runner的时候 我们runner的时候 也需要拿到我们原始组件的一个run 可以去修改我们渲染的一个输出 嗯比如说我们origin还render对吧 那么我们这边可以拿到渲染的结果 我们只不过在渲染结果之前去包裹了一层 所以说我们就可以看到这些特性 我们是允许 我们是允许我们AHOC中 通过this的方式来去访问 我们包被包括组件的相关的一些属性 那么我们可以直接读取以及操作我们当前的state stay等于1for worse 但是不建议同学们去这么去做 那么我们可以通过呃 还可以通过我们super the render方法 是不是render方法来去获取我们组件传入的render 可以有选择的去劫持渲染 啊这是呃 以及我们可以劫持生命周期的相关方法哦 就像我们上面所讲述的这个例子好 那么我们看看怎么去读取 读取以及操作我们原始人原state 那么同学们可以思考一下 你有过这样的一些尝试吗 我们来看看这个例子 在这个例子中呢 我们定义HOC 那么在ROC当中 我们会在当前come on的demount这样一个阶段当中 我们会去呃修改就修改翻译state 比如有个enhanced and true啊 我们去完成这样的一个修改 那么哦我们相当于又嗯修改完之后 我们又掉了我们当前的did did mount 这样一个周期啊 那么我们呃首先会调我们origin runner 拿到我们原始组件的一个渲染效果之后呢 我们是因为在当前组件当中 我们是增强了state对吧 增强state有这样一个呃enhanced 所以说我们就最终返回 结果是会包含一个enhanced 我们state这是去完成了我们state的相关的读取 读取的一个和操作的相关逻辑 我们也可以去做一些相关条件的一些渲染 去做相关条件的渲染 比如说我们会存在render的时候 在render时候呢 我们会看当前purpose 如果PSE是is is visible 如果好is vasiable 是我们force的话 我们会进行走到当前这个逻辑当中 Component is hahahadn't 否则的话我们就调用我们当前副组件去渲染 让你复制件的逻辑 这是比较简单的一个条件渲染 那么我们比较重要的一个就是可以去修改 我们当前right sho 比如说我们其实是可以去修改呃 呃我通过修改purpose或者修改 我们可以修改子元素 那么我们可以去统一注入相关的场景啊 包括一些额外的元素啊 以及我们为我们组件添加的红色圆框啊等等 都是可以的 我们通过调用我们rag 调用我们right children 那么在REACUN当中呢 并列当前的children 那么我们去克隆克隆求相关的所有的求职内容 这是我们对当前数的一个克隆哦 组件数的一个克隆的一个效果 我们再看看其他的例子 其他例子我们可以去修改当前render这个效效果 我们 继续看个例子 我们在run当中 我们拿到我们原始的原始组件的tat 那么我们可以定义一下我们new purpose 就如果我们当前的tree存在 并且呢如果我们当前的tree 它的一个type是我们的input 那么我们就会在当前的new purpose 它的will我们给它 比如说一个默认值 想os moted the file去修改它的属性 那么我们 重新去修改一下的purpose 我们一开始treat purpose 以当前新的purpose好 这样的话我们最终再去形成 形成一个NEUTR 通过我们克隆element 我们以及当前克隆当前的TRI 以及给到它的purpose啊 以trade propose children啊 这样的话我们就会克隆一个呃neutral 最终我们return当前neutral 这样的话我们就会渲染当前最新的tree 所以我们说会不会发现它的权限是非常高的 对不对 我们可以去拿到之前的tree tree 以及我们可以去修改原来的tree 最终返回修改之后的tree 所以说是权限是非常高的 另外我们也可以去进行相应的去处理 rough的转发 就是rap的转发 比如说我们当前呃with forword rap 那么我们最终会拿到当前rap 那么我们会在我们当前组建的rap rap属性上面去添加我们rap 所以这是通过处理我们rap转发的 这样一个逻辑好 这是我们大概的一个反向继承的相关逻辑啊 那么我们这的我们的属性代理和反向继承 它们都是属于高阶组件 那么它们两者之间又又有怎样的区别呢 它们两者之间又是怎样的区别呢 我们HOC的本质 其实它们都是接收一个组组件对吧 作为我们的入餐 那么返回一个新组件是是不是 这是它们的本质 也是它们的相同之处 就是无论这两个是储存代理啊 还是我们的反反向继承啊 其实它们都是符合这样一个定义的 那么我们水平代理 它是通过组合的方式来去进行 增强我们的相关的组件啊 而法院继承呢它是通过继承的方式那么去 但是呢他的权限是非常高的哦 他可以去修改访问组件内部的生命周期修改 拿到他的propose state 然后去修改当前的treat渲染的内容对吧 所以说它整个权限是非常高的 那么哦这是也是他们各自加上特性 一个是从组合出发 比如说我们属性耐力就是从组合出发 然后从我们外部拿到对应的web component 但是呢我们不会对web component来做各做修改 我们只会对操作我们当前purpose 我们可以对当前purpose来去做一些增删改 这样的一些相关的逻辑 所以说呃我们针对他的一个操作 就是哦是权限是比较低的对吧 而反应继承就是从我们继承的角度出发 因为我们是继承 继承的话 就可以通过super的方式来访问到 原来组件的内部的一些逻辑 我们这样的话就可以去操作live state 去拿到我们生命周期 然后进行我们render之后的一个 拿到那个render tree对吧 所以它的功能是非常强大的好 这是我们这样一个例子 这样一对比
