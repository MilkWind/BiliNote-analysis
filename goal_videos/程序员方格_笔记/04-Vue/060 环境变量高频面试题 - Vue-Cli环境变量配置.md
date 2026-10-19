# Vue-Cli 环境变量配置与 Vite 对比面试题解析

## 目录
- Vue 2 与 Vue 3 环境变量配置的三大区别
- 配置文件差异详解
- 启动与打包命令配置
- 环境变量调用方式对比
- 实操演示与问题排查
- 核心总结与注意事项
- AI 总结

## Vue 2 与 Vue 3 环境变量配置的三大区别 *Content-[00:01]
在 Vue 2 (基于 Vue-Cli) 项目中，环境变量的配置逻辑与 Vue 3 (基于 Vite) 基本一致，但在具体实现细节上存在三个核心区别。掌握这些区别是前端面试中关于构建工具和环境变量配置的高频考点。

## 配置文件差异详解 *Content-[00:09]
环境变量的配置文件命名规则在两个版本中相似，但变量前缀有严格区分。
- **文件命名**：均以 `.env` 开头，例如 `.env.development`（开发环境）、`.env.test`（测试环境）、`.env.production`（生产环境）。
- **变量前缀**：
  - **Vue 2 (Vue-Cli)**：环境变量前缀必须是 `VUE_APP_`。例如：`VUE_APP_BASE_API`。
  - **Vue 3 (Vite)**：环境变量前缀必须是 `VITE_`。例如：`VITE_BASE_API`。
在配置 Vue 2 项目时，需要将变量前缀统一修改为 `VUE_APP_`，其他内容（如具体的键值对）则与 Vite 配置基本相同。

## 启动与打包命令配置 *Content-[01:01]
在 `package.json` 中，Vue-Cli 项目的启动和打包命令与 Vite 存在明显差异。Vue-Cli 依赖 `vue-cli-service` 来执行相关操作，并且需要通过 `--mode` 参数来指定环境。
标准的命令配置如下：
- **开发环境 (dev)**：`vue-cli-service serve --mode development`
- **测试环境 (test)**：`vue-cli-service serve --mode test`
- **生产环境 (build)**：`vue-cli-service build --mode production`
在面试或实际开发中，务必注意 `vue-cli-service` 的拼写以及 `--mode` 参数的标准写法。

## 环境变量调用方式对比 *Content-[01:58]
这是 Vue 2 和 Vue 3 在环境变量使用上最核心的区别，也是面试中最容易被问到的细节。
- **Vue 2 (Vue-Cli)**：使用 Node.js 的 `process` 对象进行调用，格式为 `process.env.VUE_APP_XXX`。
- **Vue 3 (Vite)**：使用 ES 模块的 `import.meta` 对象进行调用，格式为 `import.meta.env.VITE_XXX`。

**代码调用示例 (Vue 2)**：
在 Vue 组件的 `mounted` 生命周期中读取环境变量：
```javascript
export default {
  mounted() {
    // 读取接口地址
    const apiUrl = process.env.VUE_APP_BASE_API;
    // 读取当前环境名称
    const envName = process.env.VUE_APP_ENV;
    // 读取项目名称
    const projectName = process.env.VUE_APP_TITLE;
    
    console.log(apiUrl, envName, projectName);
  }
}
```

## 实操演示与问题排查 *Content-[03:48]
在实际配置过程中，可能会遇到一些常见的错误，以下是详细的排错过程：

### 1. 变量读取结果为 undefined
- **现象**：运行 `npm run dev` 启动开发环境后，控制台输出的接口地址、当前环境、项目名称均为 `undefined`。
- **原因**：仅在配置文件中写了代码，但忘记在项目根目录下实际创建对应的 `.env.development` 等环境变量文件。
- **解决**：在项目根目录创建 `.env.development`、`.env.test`、`.env.production` 三个文件，并写入相应的 `VUE_APP_XXX` 变量。重新运行后，变量即可成功读取。

### 2. 测试环境启动报错/警告
- **现象**：运行 `npm run test` 切换到测试环境时，控制台出现警告，提示 `process.env.NODE_ENV` 与内置变量存在冲突。
- **排查**：检查 `package.json` 中的 `--mode test` 配置无误。问题出在代码中额外读取了 `process.env.NODE_ENV`。Vue-Cli 内部已经通过 `NODE_ENV` 来控制构建模式，手动读取或修改可能会引发冲突。
- **解决**：删除代码中多余读取 `NODE_ENV` 的逻辑，避免与 Vue-Cli 内置的环境变量产生冲突。再次运行 `npm run test` 后，警告消失，环境变量正常读取。

### 3. 生产环境打包验证
- **操作**：运行 `npm run build` 进行生产环境打包。
- **验证**：打包完成后，进入 `dist` 目录，在生成的 JS 文件中搜索相关关键字。可以清晰地看到，代码中的 `process.env.VUE_APP_XXX` 已经被 Webpack 在构建时静态替换为了生产环境对应的具体字符串值（如生产环境的接口前缀、环境名称等）。

## 核心总结与注意事项 *Content-[10:43]
在准备前端面试时，关于环境变量配置需要牢记以下核心结论：
1. **构建工具差异**：Vue-Cli (Vue 2) 和 Vite (Vue 3) 的环境变量读取方式完全不同。
2. **API 区分**：Vue-Cli 使用 `process.env`，而 Vite 使用 `import.meta.env`。
3. **前缀区分**：Vue-Cli 要求 `VUE_APP_` 前缀，Vite 要求 `VITE_` 前缀。
面试官通常会通过这些问题来考察候选人对不同构建工具底层原理和配置细节的掌握程度，务必准确区分，避免混淆。

## AI 总结
本视频详细讲解了 Vue 2 (Vue-Cli) 项目中环境变量的配置方法，并重点对比了其与 Vue 3 (Vite) 的三大核心区别：配置文件变量前缀（`VUE_APP_` vs `VITE_`）、启动打包命令（`vue-cli-service` vs `vite`）以及代码调用方式（`process.env` vs `import.meta.env`）。视频还通过实操演示了环境变量的配置过程，并分享了两个常见问题的排查经验：一是未创建 `.env` 文件导致变量读取为 `undefined`，二是代码中读取 `NODE_ENV` 导致与内置变量冲突的报错。内容紧贴前端面试高频考点，具有很强的实战指导意义。

---

## 文稿转写

咱们再来看V12加CLI的VUE2项目中 环境变量配置和V3加V的基本一致 只有三个区别 配置文件不同 均以VUEE开头啊 在这里咱们就把V3的给塞过来 然后改改就行啊 好对应的C过来 这是开发环境的 放到这里 然后前缀需要改一下 改成VUE 没有E别的就不用动了 这是区别 测试环境 V u e u e u e 然后还有生产环境 UE好了 然后启动打包命令不同VR项目中的窗 那排队age点JSON中呢 它和这个V3的不一样 有区别和weight啊 准确来说咱们来看一下 找到咱们V2的pack is点JASON配置 这个呢是我提前已经配置好的 它变成了这样了 是v u e CLI service 然后server mod d v mode test啊 咱们还是用个标准的写法啊 d development开发环境 然后这个呢是测试环境 这个呢是咱们的那个PRE 咱不要啊 好DEV开发环境 test的测试环境 build呢是咱们的生产环境 它是这么配置的 我给大家放到 笔记上好了 然后调用环境变量的方式也不同 V2呢它是这么调用的 它不再用import metin v了 而直接用process in v去调用 咱们来看一下啊 在V2里面找到咱们的V2app script export default 那这里咱们来一个mounted 来接口地址 Process 点上EV点上VUE下划线 app下划线 base下划线AAPI啊 他是这么读的 用的是process啊 不再是import meta了 那我们再来读点当前环境 当前环境 这个咱直接叫做APP下面的ENVENV 好说明问题就行 咱们还有一个还有一个什么没读嘞 我看一下啊啊还有一个这个name项目名称没读 也给它读出来得了 好读一下 项目名称process点in v点上 这里需要改啊 改成VUE保存 那我们来测一下 看看配置的耗时不找到 这是咱们V3的 关掉 好先来看开发环境npm run dev 稍等一下 好启动成功 8082 看控制台哦 都是undefined 那就说明读的不对啊 咱们就来检查一下吧 接口地址环境 当前环境环境名称都是undefined的 那就是哪里写错了啊 首先咱们来验证一下 这是VR的项目 然后在app里面咱做的读取哎 咱的环境变量文件哪去了 这几个变量是不是没环境变量 是不是没创建呀 刚刚只是在笔记上写了 然后呢 咱们代码里没写啊 好再来创建一下三个文件 没创建文件根目录 第一个是在开发环境的环境配置 把代码拿过来哦 再来创建第二个 第二个是测试环境的 再来看第三个production 保存好三个环境变量 文件完毕 我们再来走一遍哈 好启动完毕 8082 你看现在是不是有了呀 测试 这是咱们的development 就是咱们的当前的开发N开发环境 还有项目名称 还有你的接口前缀 然后我们再来切一个环境 咱们就切到测试环境 N p m run test 8082 再来看测试 怎么没东西了呢 这里 是这个命令有问题吗 怎么哎 这里有个警告 怎么啊 这里有个井啊 process点in v Node in v 咱们看一下是这里哪里配置的有问题啊 哎呦好 关掉它 来全屏检查一下哈 这里有个警告 V o e c r n service 然后server杠杠mode test 这里配的应该是没有问题啊 Development 然后test测试环境应该是没有问题 然后这里的话呢更没问题了 咱们刚刚呢是已经读取成功了啊 然后测试环境唯独有问题 再来起一遍 好n p m run test 还是有警告 这个警告是什么意思呢 Value process in v Node in v 看一下好还是没出来 那咱们先把这个test给跳过 先来看一下咱们的生产环境有没有问题啊 Npm run 稍等啊 他正在打包 版本的啊啊这里有可能是版本的问题 一会再说啊 打包完毕以后 我们来DISS目录看一下JS文件里面app好 你搜索一个关键字 咱们看你看不用搜了 这不看到了吗 这不就是生产环境的吗 还有当前环境 你看这个log 那么还有什么项目名称 我的VEE项目正式办对吧 然后呢这个是没有问题的 然后这个测试环境有点问题 咱们再来看一下这个测试环境啊 清空掉npm run test 通过报错信息只能排查了 好8082再来看一下哈 还是有这个报错 刷新还是没有出来 咱们来排查吧 来咱们看一下这个报错啊 他的意思就是这个值呢和你内置的有冲突 但这里呢其实我也没有用node n v 咱们这里配的是一个ENV 但是没有NO的啊 那我知道了 那有可能 这里啊这里有一个node in v 咱把这个代码删掉啊 这个代码呢咱现在用不上 干掉它不用 好咱们再来启动一下 好我们再来看一下能不能读取到 这不就好了吗 这个报错也没有了 就是那段代码之间呢有一个冲突 用到了一个node in v啊 咳这样的话呢三个环境就都没有问题了啊 然后呢咱们把这个好 把咱们读取的方式也放到这里 你注意啊 V2和V3不是weight和CRI的 读取方式不一样 VUECR呢用的是process 而weight呢用的是import meta 不一样啊 这是它们weight和CRA的三个区别 一定要注意啊 那么接下来的话呢咱们
