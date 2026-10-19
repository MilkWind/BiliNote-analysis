## 目录
- [1. 基于 XMLHttpRequest 实现 Ajax 请求概述](#1-基于-xmlhttprequest-实现-ajax-请求概述)
- [2. 实现 Ajax 请求的核心步骤](#2-实现-ajax-请求的核心步骤)
- [3. GET 请求的完整代码实现与调用](#3-get-请求的完整代码实现与调用)
- [4. POST 请求的完整代码实现与调用](#4-post-请求的完整代码实现与调用)
- [AI 总结](#ai-总结)

## 1. 基于 XMLHttpRequest 实现 Ajax 请求概述 *Content-[00:00]

- **考察目的**：在前端面试中，通过手写 Ajax 请求来考察候选人对 `XMLHttpRequest` 对象特性和特点的理解程度，从而加深对 Ajax 底层原理的认识。
- **核心概念**：`XMLHttpRequest` 是浏览器原生提供的一个 API，它允许在 JavaScript 环境中直接发送 HTTP 请求，是实现 Ajax（Asynchronous JavaScript and XML）功能的核心基础。

## 2. 实现 Ajax 请求的核心步骤 *Content-[01:17]

基于 `XMLHttpRequest` 实现一个完整的 Ajax 请求，通常需要严格遵循以下五个核心步骤：

1\. **创建 XMLHttpRequest 对象**
   - 直接通过 `new` 关键字实例化浏览器提供的 API。
   - 代码示例：`const xhr = new XMLHttpRequest();`

2\. **配置请求**
   - 使用 `xhr.open()` 方法进行请求的初始化配置。
   - 需要传入三个主要参数：
     - `method`：HTTP 请求方法，常见的包括 `GET`、`POST`、`PUT`、`DELETE` 等。
     - `url`：请求的目标地址。
     - `async`：布尔值，标识是否采用异步方式发送请求（通常设置为 `true`）。

3\. **设置请求头**
   - 使用 `xhr.setRequestHeader(key, value)` 方法设置 HTTP 请求头。
   - 常见场景：设置 `Content-Type` 为 `application/json`，以告知服务器发送的数据格式。

4\. **设置回调函数**
   - 监听 `xhr.onreadystatechange` 事件（注意全小写），用于获取请求的状态和结果。
   - 在回调函数中需要判断两个关键属性：
     - `xhr.readyState === 4`：表示请求操作已完成。
     - `xhr.status === 200`：表示服务器响应成功。

5\. **发送请求**
   - 使用 `xhr.send(data)` 方法正式发送请求。
   - 如果是 `GET` 请求，通常传入 `null`；如果是 `POST` 请求，则传入需要发送的具体数据。

## 3. GET 请求的完整代码实现与调用 *Content-[04:56]

在理清核心步骤后，可以封装一个通用的 GET 请求函数，并包含完善的异常处理机制。

- **函数封装逻辑**：
  - 定义函数 `ajaxGet(url, callback)`。
  - 创建 `XMLHttpRequest` 对象并调用 `open('GET', url, true)`。
  - 配置 `onreadystatechange` 回调：
    - 当 `readyState === 4` 时，进一步判断 `status`。
    - 若 `status === 200`，则执行成功回调：`callback(null, xhr.responseText)`。
    - 若状态码非 200，则抛出异常并执行失败回调：`callback(new Error('请求失败'), xhr.status)`。
  - 最后调用 `xhr.send(null)` 发送请求。

- **调用示例与结果处理**：
  ```javascript
  ajaxGet('http://api.example.com/data', function(error, response) {
      if (error) {
          // 处理异常情况，打印错误信息
          console.error('请求异常:', error.message);
      } else {
          // 处理成功情况，使用响应数据
          console.log('请求成功:', response);
      }
  });
  ```

## 4. POST 请求的完整代码实现与调用 *Content-[08:17]

POST 请求的实现逻辑与 GET 请求基本一致，但关键区别在于**需要设置请求头**以及**在 send 方法中传递数据**。

- **函数封装逻辑**：
  - 定义函数 `ajaxPost(url, data, callback)`。
  - 创建对象并调用 `open('POST', url, true)`。
  - **关键步骤**：调用 `xhr.setRequestHeader('Content-Type', 'application/json')` 设置请求头格式。
  - 配置 `onreadystatechange` 回调（状态判断逻辑与 GET 请求完全相同）。
  - 调用 `xhr.send(JSON.stringify(data))` 发送序列化后的数据。

- **调用示例与结果处理**：
  ```javascript
  const postData = { name: 'test', value: 123 };
  
  ajaxPost('http://api.example.com/submit', postData, function(error, response) {
      if (error) {
          console.error('POST请求异常:', error.message);
      } else {
          console.log('POST请求成功:', response);
      }
  });
  ```

## AI 总结

本视频详细讲解了前端面试中的经典场景题：如何基于原生的 `XMLHttpRequest` 对象手动实现 Ajax 请求。笔记系统梳理了实现 Ajax 的五个标准步骤（创建对象、配置请求、设置请求头、监听状态回调、发送请求），并分别提供了带有错误处理机制的 GET 和 POST 请求的完整代码封装示例。掌握这一底层原理不仅有助于应对大厂面试中的手写代码环节，更能帮助开发者深刻理解现代前端网络请求库（如 Axios）的底层运行机制。

---

## 文稿转写

好同学们大家好 接下来我们来看一下如何基于我们XML app request 来去实现我们这样一个AJAX请求 我们都知道啊 我们阿贾克斯是中基于我们xl a h p request 来去进行实现的对吧 那么所以说这个针对阿贾克斯这个题目 我们会通过这种熟悉的方式去进行一个考察 这样的话 能够让同学们对阿里S有个更好的理解 所以我们就需要清楚xl i t t request 它本身需要具备有哪些特性 它有怎样的一个特点 我们都需要去了解 所以通过这个题目呢哦这样一个手写题目呢 同学们就能够对阿贾斯有更好的 更深的一个是一个认识 那么我们来看看啊 因为我们XML h p request request是我们现浏览器提供这样一个AAPI对吧 它能够在我们JS环境当中去进行发送 对应的AHP请求 我们通过它实现一个 我们的阿贾克斯这样的功能 那么所以说我们接下来看一看 如何去实现这样一个呃 通过HTML keith p request实现 是实现一个汉贾克斯呢 我们来右侧方式去给他们去演示一下 对应的相关的一些细节 也是同学们需要重点去学习的 首先我们就需要第一步需要创建对应的XML对象 叉一叉对象 我们就直直接去通过new的方式 因为它就是浏览器的AAPI 所以我直接通过呃new我们x l ATP quest 之后 第二步去进行配置请求 配置对应的请求 那么我们通过XML open的方式去传入对应的 传入对应的message 以及传入对应的URO 还有传入对应的think是否think啊 这种标识 这是哦我们基本的是第二步 第三步呢 因为我们上部它method就对应的方法 这同学们应该都比较熟悉啊 method对应我们ATP请求的方法 就是它包含我们的比如get呀post啊 我们的put啊 Delete delete呀对吧 这几种方法 第UL就我们请求的地址 那a think呢就是是否异步 所以我们需要提供这样的一个能力好 那么第三步呢 就需要我们需要设置对应的请求头 我们设置最终的一个请求头 那么请请求头怎么设置呢 其实也是利用我们叉叉叉它的open or reverse 它的一个set request header Set cross header 我们的KEV的方式 key就是对应的content type 那么V就是对应的当前的一个格式 比如说我们常设置对应的application jason 好通过这种方式来去设置我们当前进镜头 那么第四步呢就是设置我们的回调函数 设置回调函数 那么哦什么回调函数呢 就是我们在发起对应的请求以后啊 我们需要啊知道当前请求的一个结果 一个状态对吧 就是需要监听我们 On ready state change 记住我就是全小写的unrealistation function 那么在此当中去啊监听 比如说通过我们的呃叉一叉 它对应的ready st 这样一个对象它有几个状态 我们根据不同的状态 比如说四啊说明请求完成 还有它的我们X1XR的values 如果是200 说明就啊说明就成功响应 那么这是第四步 第五步呢我们直接就发送请求 发送请求就是我们查一下ASSEND 然后我们刚刚发对应的数数据data好 这是我们理了一下对应的相关步骤哦 接下来我们看一下它对应的一个完整的实例啊 我们理完步骤以后啊 好再去写这个我们的实例 我就发现非常简单了 就按照刚刚的我们的步骤按JX 比如说get呀 我们提供UL以及对应的call back 好我们提先实现一个RES的get请求 就像刚刚所说的 我们先第一步先创建创建一个叉叉对象 好 第二步呢 我们就是呃通过open的方式去配置对应的请求 我们当前的配置对应的get及当前的URL参数 就是我们传进来的参数以及对应处 我们实现一个它是一个异步的 并且我们第四步自己使用 这是第四步好 如果不需要设置请求头的话啊 我们定义我们当当前回调就on ready is exchange 在当中去看看成功是否是否成功与否 等于四说明请求成功 然后查一查我们的studies 等于200 说明就OK了 就四的话就是我们请求完成 然后200的话就是我们成功响应 好那么在200当中呢 我们就需要在显应当中 我们是不是执行我们的call back呀 通过家庭pass再去咨询一下我们 它我们响应的response test 然后去给到我们call back 好这样如果else啊还可以提供对应的else啊 就相相当于讲议程嘛 讲异常 我们第一个参数呢就需要抛出对应的异常 比如说我们new error一下 然后以及对应的相关的异常信息 比如请求失败 那么也可以再去请失败当中去返回对应的 它的一个状态 好那么这是对应那个回回调 那么最后一步什么 我们是不是send呀 发送对应的数据 防止等于出去 是不是就OK了 这是我们简单的一个get请求 那么最终我们怎么是怎么用呢 我们就按下get以及用AT比ATP4 对哪个地址 然后回调用function1开始就是我们error的相关的信息 然后呢最后是我们成功的相关的信息 我们需要判断一下 如果error存在 那么说明就异常了 那么我们就比如说抗酸抗衰弱 否则就成功 好这是我们针对这样的get请求 那么我们post的请求呢 副词牛牛 其实我们可以设置对应的header 以及传入对应的data 以及我们设置对应的header 你把核心的都都拿过来 就set我们request header 我们设置我们对应的content type 祝我们application jason 好send的时候呢 就需要传入我们相关的数据 那这样的话就实现了我们当前的post请求 那么怎么去调用呢 我们需要在第二项中传入对应相关数据 然后之后再最后一项就我们对应的call back 跟我们上述内容是一样的 所以这是针对post的请求相关的点了好 这是我们针对如何基于它们l a h p request 来实现对应的一个阿贾克斯请求对象 这样一个题目
