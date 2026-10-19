## 目录
- 引言与背景介绍 *Content-[00:00]
- XMLHttpRequest 实现 Ajax 的核心步骤 *Content-[01:17]
- GET 请求的完整封装与调用实例 *Content-[04:56]
- POST 请求的完整封装与调用实例 *Content-[08:17]
- AI 总结

## 引言与背景介绍 *Content-[00:00]
- 探讨如何基于 `XMLHttpRequest` 对象实现 Ajax 请求。
- Ajax 是基于 `XMLHttpRequest`（简称 XHR）实现的，通过手写实现该功能，可以加深对 Ajax 底层原理的理解。
- `XMLHttpRequest` 是浏览器原生提供的 API，允许在 JavaScript 环境中发送 HTTP 请求，从而实现 Ajax 功能。

## XMLHttpRequest 实现 Ajax 的核心步骤 *Content-[01:17]
实现一个完整的 Ajax 请求通常包含以下五个核心步骤：

1\. **创建 XMLHttpRequest 对象**
- 直接通过 `new XMLHttpRequest()` 实例化对象，因为它是浏览器提供的原生 API。

2\. **配置请求**
- 使用 `xhr.open(method, url, async)` 方法进行配置。
- `method`：HTTP 请求方法，如 `GET`、`POST`、`PUT`、`DELETE` 等。
- `url`：请求的目标地址。
- `async`：布尔值，标识是否进行异步请求（通常设置为 `true`）。

3\. **设置请求头**
- 使用 `xhr.setRequestHeader(key, value)` 方法设置 HTTP 请求头。
- 常见的设置如指定数据格式：`key` 为 `Content-Type`，`value` 为 `application/json`。

4\. **设置回调函数**
- 监听 `xhr.onreadystatechange` 事件，用于获取请求的结果和状态。
- 在回调函数中需要判断两个关键状态：
  - `xhr.readyState === 4`：表示请求已完成。
  - `xhr.status === 200`：表示响应成功。
- 当状态满足条件时，通过 `JSON.parse()` 解析 `xhr.responseText` 并处理响应数据；若不满足，则处理异常（如抛出 `new Error('请求失败')` 并返回对应的状态码）。

5\. **发送请求**
- 使用 `xhr.send(data)` 方法发送请求，`data` 为需要传递的请求体数据（GET 请求通常传 `null`）。

## GET 请求的完整封装与调用实例 *Content-[04:56]
基于上述步骤，可以封装一个通用的 GET 请求函数：

- **函数封装细节**：
  - 接收参数：`url`（请求地址）和 `callback`（回调函数）。
  - 实例化 XHR 对象并调用 `open('GET', url, true)`。
  - 设置 `onreadystatechange` 回调：
    - 若 `readyState === 4` 且 `status === 200`，则解析 `responseText` 并执行 `callback(null, data)`。
    - 若请求失败，则执行 `callback(new Error('请求失败'), status)`。
  - 最后调用 `send(null)` 发送请求。

- **代码示例**：
```javascript
function get(url, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', url, true);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                callback(null, data);
            } else {
                callback(new Error('请求失败'), xhr.status);
            }
        }
    };
    xhr.send(null);
}
```

- **调用示例**：
```javascript
get('https://httpbin.org/get', function(error, data) {
    if (error) {
        console.error(error);
    } else {
        console.log('请求成功:', data);
    }
});
```

## POST 请求的完整封装与调用实例 *Content-[08:17]
POST 请求的封装与 GET 类似，但需要额外处理请求头和数据传递：

- **函数封装细节**：
  - 接收参数：`url`（请求地址）、`data`（请求体数据）和 `callback`（回调函数）。
  - 实例化 XHR 对象并调用 `open('POST', url, true)`。
  - **关键区别**：必须使用 `setRequestHeader` 设置 `Content-Type` 为 `application/json`。
  - 设置 `onreadystatechange` 回调，逻辑与 GET 请求一致。
  - 调用 `send(data)` 发送请求，将序列化后的数据传入请求体中。

- **代码示例**：
```javascript
function post(url, data, callback) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url, true);
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4) {
            if (xhr.status === 200) {
                const res = JSON.parse(xhr.responseText);
                callback(null, res);
            } else {
                callback(new Error('请求失败'), xhr.status);
            }
        }
    };
    xhr.send(JSON.stringify(data));
}
```

- **调用示例**：
```javascript
post('https://httpbin.org/post', { key: 'value' }, function(error, data) {
    if (error) {
        console.error(error);
    } else {
        console.log('请求成功:', data);
    }
});
```

## AI 总结
本视频详细讲解了如何基于浏览器原生 API `XMLHttpRequest` 手动实现 Ajax 请求。内容从核心原理出发，拆解了创建对象、配置请求、设置请求头、监听状态回调以及发送数据的五个标准步骤。随后，通过具体的代码实战，分别演示了 GET 和 POST 请求的封装过程，重点强调了 POST 请求中 `Content-Type` 请求头的设置以及请求体数据的传递。掌握这些底层手写逻辑，有助于前端开发者在面试中更好地应对场景题，并深刻理解现代网络请求库（如 Axios）的底层运行机制。

---

## 文稿转写

好同学们大家好 接下来我们来看一下如何基于我们XML app request 来去实现我们这样一个AJAX请求 我们都知道啊 我们阿贾克斯是中基于我们xl a h p request 来去进行实现的对吧 那么所以说这个针对阿贾克斯这个题目 我们会通过这种熟悉的方式去进行一个考察 这样的话 能够让同学们对阿里S有个更好的理解 所以我们就需要清楚xl i t t request 它本身需要具备有哪些特性 它有怎样的一个特点 我们都需要去了解 所以通过这个题目呢哦这样一个手写题目呢 同学们就能够对阿贾斯有更好的 更深的一个是一个认识 那么我们来看看啊 因为我们XML h p request request是我们现浏览器提供这样一个AAPI对吧 它能够在我们JS环境当中去进行发送 对应的AHP请求 我们通过它实现一个我们的阿贾克斯 这样一个功能 那么所以说我们接下来看一看 如何去实现这样一个呃 通过HTML q HT request实现 是实现一个汉贾克斯呢 我们来右侧方式去给他们去演示一下 对应的相关的一些细节 也是同学们需要重点去学习的 首先我们就需要第一步需要创建对应的XML对象 叉一叉对象 我们就直直接去通过new的方式 因为它就是浏览器的AAPI 所以我直接通过呃new我们x l ATP quest 之后 第二步去进行配置请求 配置对应的请求 那么我们通过XML open的方式去传入对应的 传入对应的message 以及传入对应的URO 还有传入对应的think是否think啊 这种标识 这是哦我们基本的是第二步 第三步呢 因为我们上部它method就对应的方法 这同学们应该都比较熟悉啊 method对应我们ATP请求的方法 就是它包含我们的比如get呀post啊 我们的put啊 Delete delete呀对吧 这几种方法 第UL就我们请求的地址 那a think呢就是是否异步 所以我们需要提供这样的一个能力好 那么第三步呢 就需要我们需要设置对应的请求头 我们设置最终的一个请求头 那么请请求头怎么设置呢 其实也是利用我们叉叉叉它的open or reverse 它的一个set request header Set cross header 我们的KEV的方式 key就是对应的content type 那么V就是对应的当前的一个格式 比如说我们常设置对应的application jason 好通过这种方式来去设置我们当前进镜头 那么第四步呢就是设置我们的回调函数 设置回调函数 那么哦什么回调函数呢 就是我们在发起对应的请求以后啊 我们需要啊知道当前请求的一个结果 一个状态对吧 就是需要监听我们 On ready state change 记住我就是全小写的unrealistation function 那么在此当中去啊监听 比如说通过我们的呃叉一叉 它对应的ready st 这样一个对象它有几个状态 我们根据不同的状态 比如说四啊说明请求完成 还有它的我们X1XR的values 如果是200 说明就啊说明就成功响应 那么这是第四步 第五步呢我们直接就发送请求 发送请求就是我们查一下ASSEND 然后我们刚刚发对应的数数据data好 这是我们理了一下对应的相关步骤哦 接下来我们看一下它对应的一个完整的实例啊 我们理完步骤以后啊 好再去写这个我们的实例 我就发现非常简单了 就按照刚刚的我们的步骤按JX 比如说get呀 我们提供UL以及对应的call back 好我们提先实现一个RES的get请求 就像刚刚所说的 我们先第一步先创建创建一个叉叉的对象 好 第二步呢 我们就是呃通过open的方式去配置对应的请求 我们当前的配置对应的get及当前的URL参数 就是我们传进来的参数以及对应处 我们实现一个它是一个异步的 并且我们第四步自己使用 这是第四步好 如果不需要设置请求头的话啊 我们定义我们当当前回调就on ready is this change 在当中去看看成功是否是否成功与否 等于四说明请求成功 然后查一查我们的studies 等于200 说明就OK了 就四的话就是我们请求完成 然后200的话就是我们成功响应 好那么在200当中呢 我们就需要在显应当中 我们是不是执行我们的call back呀 通过家庭pass再去咨询一下我们 它我们响应的response test 然后去给到我们call back 好这样如果else啊还可以提供对应的else啊 就相相当于讲议程嘛 讲异常 我们第一个参数呢就需要抛出对应的异常 比如说我们new error一下 然后以及对应的相关的异常信息 比如请求失败 那么也可以再去请失败当中去返回对应的 它的一个状态 好那么这是对应那个回回调 那么最后一步什么 我们是不是send呀 发送对应的数据 防止等于出去 是不是就OK了 这是我们简单的一个get请求 那么最终我们怎么是怎么用呢 我们就按下get以及用AT比ATP4 对哪个地址 然后回调用function1开始就是我们error的相关的信息 然后呢最后是我们成功的相关的信息 我们需要判断一下 如果error存在 那么说明就异常了 那么我们就比如说抗酸 抗酸入 否则就成功 好这是我们针对这样的get请求 那么我们post的请求呢 构词牛其实我们可以设置对应的header 以及传入对应的data 以及我们设置对应的header 你把核心的都都拿过来 就set我们request header 我们设置我们对应的content type 祝我们application jason 好send的时候呢 就需要传入我们相关的数据 那这样的话就实现了我们当前的post请求 那么怎么去调用呢 我们需要在第二项中传入对应相关数据 然后之后再最后一项就我们对应的call back 跟我们上述内容是一样的 所以这是针对post的请求相关的点了好 这是我们针对如何基于它们l a h p request 来实现对应的一个阿贾克斯请求对象 这样一个题目
