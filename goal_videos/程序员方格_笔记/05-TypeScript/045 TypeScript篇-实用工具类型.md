# 2026 前端面试题合集：TypeScript 实用工具类型

## 目录
- 什么是实用工具类型
- Partial<T>：生成可选属性类型
- Readonly<T>：生成只读属性类型
- Pick<T, K>：挑选指定属性
- Omit<T, K>：剔除指定属性
- 其他常用实用工具类型扩展
- AI 总结

## 什么是实用工具类型 *Content-[00:00]
- **核心概念**：实用工具类型（Utility Types）是 TypeScript 内置的一组类型工具函数。这里的“函数”是类型概念上的描述，意味着它们可以接收一个或多个类型作为输入，并返回一个新类型作为输出。
- **底层实现**：基于 TypeScript 强大的泛型（Generics）、条件类型（Conditional Types）和映射类型（Mapped Types）等高级特性实现。
- **核心价值**：能够基于已有的类型自动地生成新的、有关联的类型变体，从而避免手动编写大量重复的类型定义。
- **常见场景**：在 TS 开发中，经常需要基于现有类型创建新类型，例如一个类型的可选版本、只读版本或只包含部分属性的版本。
- **本节重点**：聚焦四个最核心、最常用的工具类型：`Partial`、`Readonly`、`Pick` 和 `Omit`，它们分别解决了开发中最常遇到的四种类型转换需求。

## Partial\<T\>：生成可选属性类型 *Content-[01:32]
- **功能定义**：`Partial<T>` 接收一个类型泛型 `T`，返回一个新的类型。新类型拥有与 `T` 完全相同的属性，但**所有属性都变成了可选的**（属性名后面带上 `?`）。
- **典型场景**：处理部分更新的数据。
- **代码示例**：
  ```typescript
  interface User {
    id: number;
    username: string;
    email: string;
  }

  // 使用 Partial<User>，fields 的所有属性都变为可选
  function updateUser(id: number, fields: Partial<User>) {
    // 更新逻辑
  }

  // 调用示例：可以只传部分字段，也可以不传
  updateUser(1, { username: 'new_name' });
  updateUser(1, { email: 'new_email@example.com' });
  ```
- **优势对比**：如果没有 `Partial`，函数参数必须要求传入一个完整的 `User` 对象，这在实际开发中非常不灵活。`Partial` 自动完成了将所有属性转换为可选属性的过程，等价于手动为每个属性添加 `?`。

## Readonly\<T\>：生成只读属性类型 *Content-[03:09]
- **功能定义**：`Readonly<T>` 将类型 `T` 中**所有的属性都标记为只读**。一旦对象被声明为该类型，其任何属性都不能被重新赋值。
- **典型场景**：处理需要保持不变的数据，如全局配置对象，或在某些状态管理模式中确保状态是不可变的（Immutable）。
- **代码示例**：
  ```typescript
  interface Config {
    port: number;
    host: string;
  }

  // 声明为 Readonly<Config>
  const appConfig: Readonly<Config> = {
    port: 8080,
    host: 'localhost'
  };

  // 尝试修改属性会在编译阶段立即报错
  // appConfig.port = 9090; // Error: Cannot assign to 'port' because it is a read-only property.
  ```
- **核心价值**：在代码运行之前（编译阶段）就提供了数据不可变性的保证，有效防止意外的副作用。

## Pick\<T, K\>：挑选指定属性 *Content-[04:29]
- **功能定义**：`Pick<T, K>` 用于改变类型的结构。它从已有的类型 `T` 中挑选出 `K` 所指定的属性，组合成一个新的类型。这里的 `K` 通常是一个由属性名组成的联合类型（Union Type）。
- **典型场景**：从复杂的后端数据结构中提取部分字段，用于前端界面展示。
- **代码示例**：
  ```typescript
  interface User {
    id: number;
    username: string;
    email: string;
    password: string;
  }

  // 用户列表只需展示 id 和 username
  type UserPreview = Pick<User, 'id' | 'username'>;

  // listItem 必须且只能包含 id 和 username
  const listItem: UserPreview = {
    id: 1,
    username: 'alice'
  };
  ```
- **优势**：自动生成了一个精确的新类型（等价于 `{ id: number; username: string; }`），避免了手动重新定义接口，非常高效。

## Omit\<T, K\>：剔除指定属性 *Content-[05:53]
- **功能定义**：`Omit<T, K>` 是 `Pick` 的反向操作。它接收类型 `T` 和属性名联合类型 `K`，创建一个**移除了 `K` 中所有指定属性**的新类型。
- **典型场景**：数据脱敏。例如将包含敏感信息的用户对象返回给前端时，剔除密码等不该暴露的字段。
- **代码示例**：
  ```typescript
  interface UserWithPassword {
    id: number;
    username: string;
    passwordHash: string;
  }

  // 剔除 passwordHash 字段
  type PublicUser = Omit<UserWithPassword, 'passwordHash'>;

  // PublicUser 只包含 id 和 username，是一个安全的用户类型
  const safeUser: PublicUser = {
    id: 1,
    username: 'alice'
  };
  ```

## 其他常用实用工具类型扩展 *Content-[07:09]
除了上述四个核心工具类型，TypeScript 还提供了许多强大的内置工具，以下是几个常用的扩展方向：
- **Required\<T\>**：`Partial` 的反向操作，将类型中的所有可选属性变成必填属性。
- **Record\<K, T\>**：非常适合用来定义键值结构明确的对象。例如，定义一个所有键都是字符串、所有值都是数字的类型：`Record<string, number>`。
- **Exclude\<T, U\>**：作用于联合类型，用于从一个联合类型 `T` 中排除指定的成员 `U`。
- **ReturnType\<T\>**：非常实用的工具，用于自动获取一个函数类型的返回值类型。当需要复用某个函数的返回结果类型时，可以直接使用 `ReturnType<typeof myFunction>`，方便快捷。

## AI 总结
本节课深入讲解了 TypeScript 中四个最核心的实用工具类型（Utility Types）：`Partial`、`Readonly`、`Pick` 和 `Omit`。这些工具类型基于泛型和映射类型，能够基于现有类型自动生成新的类型变体，极大减少了重复的类型定义代码。`Partial` 用于将属性转为可选，适用于部分更新场景；`Readonly` 用于保证数据不可变性；`Pick` 和 `Omit` 则分别用于从复杂类型中提取或剔除特定字段，非常适合前端数据展示和后端数据脱敏。此外，课程还简要介绍了 `Required`、`Record`、`Exclude` 和 `ReturnType` 等扩展工具。熟练掌握这些工具类型，能够显著提升 TypeScript 项目的类型安全性和开发效率，是前端大厂面试和实际开发中的高频核心考点。

---

## 文稿转写

Hello 大家好 这节课我们要探讨的主题是ts的实用工具类型 那么在TS开发中呢 我们经常会遇到 需要基于现有类型创建新类型的场景 比如说一个类型的可选版本 只读版本或者只包含部分属性的版本 那么本次分享呢 我们会聚焦几个核心的最常用的工具类型 所以通过代码的示例 帮助大家理解它们的功能和适用场景 好话不多说 我们开始 首先我们要明确一个问题 就是什么是实用工具类型 简单来说呢 它就是啊TTS内置的一组类型工具函数 这里的函数是一个类型概念上的描述 它意味着他们接收 可以接收一个或者多个类型作为输入 然后返回一个新类型作为输出 这些工具的底层呢是基于TS强大的泛型啊 啊条件类型啊 和啊映射类型这些高级特性实现 它们的核心价值在于 能够基于已有的类型去自动地生成新的 有关联的类型变体 从而避免我们去手动的编写 大量重复的类型定义 那么今天呢我们会关注四个最常见的代表啊 partiread only pick和omit it 他们分别解决了开发中最常遇到的四种类型 转换的需求 接下来我们逐一拆解 好我们先来看第一个实用的工具类型PARTI 那么从字面意思部分就可以理解啊 PARTI它的作用就是接受一个类型泛型T 然后返回一个新的类型 这个新的类型拥有与T完全相同的属性 但是呢所有属性都变成了可选的 也就是属性名上面后面都会带上问号 那么它的典型应用场景 就是处理部分更新的数据 我们来看一下这里的代码 这里定义了一个user接口 然后包含三个必填的字段 接下来呢我们有一个update user函数啊 他的第二个参数fills哎 就被定义成了一个passion啊 User 这就意味着我们传递给这个函数的对象 可以包含user接口中的任意一个或者多个的字段 也可以一个都不包含 所以大家可以看到下面的调用示例 我们可以只传username来更新用户名 或者只传啊email来更新邮箱 TS的类型检查都会正常通过 那么如果啊没有趴手呢 我们就必须传入一个完整的新的user对象 这显然是非常不灵活的 所以呢啊PARTI生最终生成的类型 就等价于去我们手动定义这个user对象 他们的这个属性都带上了问号 所以pass就帮我们自动的完成了这个转换过程好 那么我们再来看看第二个工具read only 它的作用名也和名字一样直观啊 就是它的作用呢 就是将类型T中所有的属性都标记成只读 这就意味着一一旦一个对象被声明为这种类型 它的任何属性都不能被重新复制 那么这个特性呢 在处理一些需要保持不变的数据时 就非常有用啊 比如说你啊做一个全局的配置对象 或者在某些啊状态管理的模式下面呢 你用来确保你用read only 就可以确保这个状态是immutable 好我们来看一个这个这个例子 这里呢有一个CONFIG接口 然后呢我们声明了一个常量 并且呢把它指定了成了read only app configure 所以当我们修改这个configure点sing的时候 大家可以看到这个ts在编译阶段就会立即报错 提示我们这是一个可只读属性 所以这就是read only的核心价值 它在代码运行之前 就给我们啊提供了数据的不可变性的保证 所以防止意外的副作用 好前面两个工具呢都是在修改属性的修饰符 然后接下来的peek啊 则是用来改变类型的结构的 那么peek t k 它的作用就是从一个已有的类型T中 挑选出K所指定的那些属性 然后组合成一个新的属性 新的类型 这里的K呢通常是一个由属性名组成的 联合类型 所以一个非常典型的场景就是 当我们需要从一个复杂的后端数据结构中 提取部分字段 用来啊展示在前端的啊界面的时候 就是我们可以用这个pick 我们来看这段代码 我们有一个完整的user接口 还有四个属性啊 现在假设一个用户列表只用展示id和user name 我们就可以用pick给它创建一个新的类型 叫做user preview 这样一来呢 RESEARPREVIEW这个类型就只包含id和username啊 然后当我们创建一个list item变量的时候 然后指定它是这个user preview类型诶 它就必须只能包含这两个属性 所以呢peek就帮我们自动生成了一个等价于id 冒号number 然后user冒号name的呃 新的类型啊就非常精确 非常高效 好介绍完peek我们来看一下它的反向操作 omit omit it tk的作用和pk完全相反 它也是接受一个类型T和一个属性名啊 联合的类型K 但是呢它会创建一个啊 移除了K中所有指定属性的新类型 所以它的应用场景就是数据脱敏 比如说我们要将一个包含敏感数据的 敏感信息的用户对象返回给前端的时候 就可以用omit it来剔除掉 像啊像密码啊这些啊不该暴露给前端的字段 所以大家看这个例子 我们有一个user with password接口 哎 里面包含了一个password哈希 然后呢我们通过这个啊omit it 把这个哈希给排除在外 这样呢我们新的类型就啊没有这个password哈 希这样一个属性哎 所以呢啊password public user这样的类型结构啊 是一个不包含密码字段的安全用户类型 唉这就是omit it给我们提供的一个啊方法 好今天呢我们只是介绍了几种核心的啊工具 TS里面呢还有很多啊强大的工具 这里我列举几个方便大家作为延伸阅读的方向 首先是require require是passer的反向操作 它能将一个类型中的所有可选属性变成必填 然后record record就非常适合用来定义建值结构的明确对象 比如说你定义一个所有键都是字符串 所有值都是数字的类型 然后是XCLUDE 它用来啊作用是在这个联合队形联合类型上面 它可以用从一个联合类型中排除指定的成员 然后最后是return type 这是一个非常实用的工具 可以去自动获取一个函数类型的返回值啊 当我们想复用某个函数的返回结果类型时 你就可以用return type 这样方便 好以上就是今天的内容啊 希望大家能够在这个ts s项目里面去熟练的啊 使用这些工具函数工具库 我们下节课再见拜拜
