"""
Seed knowledge base with rich documents for testing
注入丰富文档以强化知识库
"""

import asyncio
from app.db.session import get_db
from app.services.knowledge_indexer import index_markdown_document
from app.db.models import UserSkillState, GeneratedQuestion, Drill, DrillSession, KnowledgeDocument, KnowledgeChunk


def main():
    db = next(get_db())

    # 清理旧数据
    db.query(DrillSession).delete()
    db.query(Drill).delete()
    db.query(GeneratedQuestion).delete()
    db.query(KnowledgeChunk).delete()
    db.query(KnowledgeDocument).delete()
    db.commit()
    print("已清理旧数据")

    # ========== 文档1: Java并发编程（丰富版）==========
    doc1 = index_markdown_document(
        db,
        user_id="default-user",
        name="Java并发编程详解",
        category="Java",
        tags=["并发", "多线程", "JVM", "面试"],
        markdown_text="""# Java并发编程

## 线程基础

Java中创建线程主要有三种方式。第一种是继承Thread类，重写run方法，这种方式简单直接但由于Java只支持单继承，所以会失去继承其他类的能力。第二种是实现Runnable接口，将任务逻辑与线程执行解耦，这是最推荐的方式。第三种是实现Callable接口，它可以返回执行结果并抛出异常，通常配合FutureTask和线程池使用。

线程有五种状态：新建（New）、就绪（Runnable）、运行（Running）、阻塞（Blocked）和终止（Terminated）。线程的start方法启动线程并调用run方法，直接调用run方法只是在当前线程中执行代码，不会创建新线程。

线程池是管理线程生命周期的最佳实践。通过Executors工具类可以快速创建线程池，包括FixedThreadPool、CachedThreadPool和SingleThreadExecutor等。但建议使用ThreadPoolExecutor手动创建，这样可以明确指定核心参数，避免资源耗尽。

核心参数包括：corePoolSize核心线程数，maximumPoolSize最大线程数，keepAliveTime空闲线程存活时间，workQueue任务队列，以及RejectedExecutionHandler拒绝策略。

## synchronized关键字

synchronized是Java中最基本的同步机制，它保证同一时刻只有一个线程可以执行被保护的代码块。synchronized有三种使用方式：修饰实例方法（锁住this对象）、修饰静态方法（锁住Class对象）、修饰代码块（锁住指定对象）。

synchronized是一个可重入锁，这意味着同一个线程可以多次获取同一把锁而不会发生死锁。锁的释放发生在方法正常返回或抛出异常时。

在JVM层面，synchronized通过monitor对象实现。Java 6之后引入了锁升级机制：无锁状态 -> 偏向锁 -> 轻量级锁 -> 重量级锁。偏向锁适用于只有一个线程访问同步块的场景，轻量级锁通过CAS操作避免线程阻塞，重量级锁则需要操作系统互斥量。

## volatile关键字

volatile是Java中最轻量的同步机制。它保证变量的可见性和有序性，但不保证原子性。当一个变量被volatile修饰时，对它的写操作会立即刷新到主内存，读操作会从主内存重新加载。这确保了所有线程看到的都是最新值。

volatile通过插入内存屏障（Memory Barrier）来禁止指令重排序。StoreStore屏障保证volatile写之前的操作不会被重排序到volatile写之后；LoadLoad屏障保证volatile读之后的操作不会被重排序到volatile读之前。

volatile适用于以下场景：状态标记变量（如shutdownRequested）、单次安全发布（如双重检查锁定中的instance变量）、简单的读写操作（如计数器，注意volatile不保证i++的原子性）。

## JUC并发工具

Java并发包（java.util.concurrent）提供了大量高级并发工具。CountDownLatch允许一个或多个线程等待其他线程完成操作，通过countDown方法递减计数器，await方法阻塞等待。CyclicBarrier让一组线程互相等待到达屏障点，与CountDownLatch不同，它可以重复使用。

Semaphore控制同时访问特定资源的线程数量，常用于限流场景。ReentrantLock是synchronized的增强替代品，支持公平/非公平锁、尝试非阻塞获取锁（tryLock）、可中断获取锁以及Condition条件变量。

## 死锁与排查

死锁产生的四个必要条件是：互斥条件（资源不能共享）、持有并等待（持有资源同时等待其他资源）、不可剥夺（已获取的资源不能被强制释放）和循环等待（资源形成环路）。

排查死锁可以使用以下方法：jstack命令导出线程栈信息，定位BLOCKED状态的线程及其持有的锁；JConsole和VisualVM提供图形化的死锁检测功能；通过ThreadMXBean的findDeadlockedThreads方法编程检测死锁。

避免死锁的策略包括：按固定顺序获取锁、使用tryLock设置超时时间、使用Lock-Free算法替代锁、减少锁的粒度。""",
    )
    print(f"文档1: {doc1.name} - {len(doc1.chunks)} 个知识块")

    # ========== 文档2: Spring框架核心==========
    doc2 = index_markdown_document(
        db,
        user_id="default-user",
        name="Spring框架核心原理",
        category="Java",
        tags=["Spring", "IoC", "AOP", "面试"],
        markdown_text="""# Spring框架核心原理

## IoC容器与依赖注入

IoC（控制反转）是Spring的核心思想，将对象的创建和管理交给容器，而不是在代码中硬编码依赖关系。Spring通过依赖注入（DI）实现IoC，主要有三种注入方式：构造器注入、Setter注入和字段注入。

ApplicationContext是Spring IoC容器的高级接口，继承自BeanFactory。它提供了Bean的实例化、配置组装、生命周期管理等功能。常用的实现类包括ClassPathXmlApplicationContext和AnnotationConfigApplicationContext。

Bean的作用域包括：singleton（默认，单例）、prototype（每次获取创建新实例）、request（每次HTTP请求一个）、session（每个HTTP会话一个）。在singleton模式下，Spring容器中只有一个共享的Bean实例。

Bean的生命周期包括：实例化 -> 属性填充 -> BeanNameAware/BeanFactoryAware回调 -> BeanPostProcessor前置处理 -> InitializingBean初始化/自定义init方法 -> BeanPostProcessor后置处理 -> 可以使用 -> DisposableBean销毁/自定义destroy方法。

## AOP面向切面编程

AOP（Aspect-Oriented Programming）允许将横切关注点（如日志、事务、安全）与业务逻辑分离。Spring AOP基于动态代理实现，对实现了接口的类使用JDK动态代理，对没有实现接口的类使用CGLIB代理。

核心概念包括：Aspect（切面，包含切点和通知）、Join Point（连接点，程序执行点）、Pointcut（切点，匹配连接点的表达式）、Advice（通知，切面在连接点执行的动作）。通知类型包括：Before、After、AfterReturning、AfterThrowing和Around。

Spring使用AspectJ注解来定义切面：@Aspect标记切面类，@Pointcut定义切点表达式，@Before/@After/@Around等定义通知。切点表达式支持within、execution、this、target、args等指示器。

## Spring事务管理

Spring提供声明式事务管理，通过@Transactional注解简化事务操作。事务的ACID特性包括：原子性（Atomicity）、一致性（Consistency）、隔离性（Isolation）和持久性（Durability）。

事务传播行为包括：REQUIRED（默认，支持当前事务，没有则新建）、REQUIRES_NEW（总是新建事务）、NESTED（嵌套事务）、SUPPORTS（支持当前事务，没有则以非事务方式运行）、NOT_SUPPORTED（挂起当前事务）、NEVER（不允许事务）、MANDATORY（必须有事务）。

事务隔离级别包括：READ_UNCOMMITTED（读未提交）、READ_COMMITTED（读已提交）、REPEATABLE_READ（可重复读）、SERIALIZABLE（串行化）。MySQL默认使用REPEATABLE_READ，Oracle默认使用READ_COMMITTED。

## Spring MVC请求处理流程

Spring MVC的核心组件是DispatcherServlet，它作为前端控制器接收所有请求。请求处理流程：客户端请求到达DispatcherServlet -> HandlerMapping找到对应的处理器 -> HandlerAdapter调用处理器方法 -> 方法返回ModelAndView -> ViewResolver解析视图 -> 视图渲染响应。

@Controller标记控制器类，@RequestMapping映射请求路径，@GetMapping/@PostMapping等是快捷映射方式。@RequestParam获取请求参数，@PathVariable获取路径变量，@RequestBody将请求体绑定到对象。

RESTful API设计中，常见的HTTP状态码：200成功、201资源创建成功、400请求参数错误、401未授权、403禁止访问、404资源不存在、500服务器内部错误。""",
    )
    print(f"文档2: {doc2.name} - {len(doc2.chunks)} 个知识块")

    # ========== 文档3: 数据库与SQL==========
    doc3 = index_markdown_document(
        db,
        user_id="default-user",
        name="MySQL性能优化与索引",
        category="数据库",
        tags=["MySQL", "索引", "SQL优化", "面试"],
        markdown_text="""# MySQL性能优化与索引

## 索引基础

索引是帮助MySQL高效获取数据的数据结构。最常见的索引类型是B+树索引，InnoDB引擎默认使用B+树。索引大大减少了存储引擎需要扫描的数据量，将全表扫描变为索引查找。

B+树的特点是所有数据都存储在叶子节点，非叶子节点只存储键值和指针。叶子节点之间有链表连接，支持范围查询的高效扫描。相比B树，B+树的查询效率更稳定，因为每次查询都要走到叶子节点。

索引分为：主键索引（Primary Key）、唯一索引（Unique）、普通索引（Index）、全文索引（Fulltext）。主键索引的叶子节点存储完整行数据，其他索引的叶子节点存储主键值（回表查询）。

## 索引优化策略

最左前缀匹配原则：复合索引(col1, col2, col3)可以支持(col1)、(col1, col2)和(col1, col2, col 3)的查询，但无法支持(col2)或(col3)的单独查询。

覆盖索引是指查询所需的所有字段都在索引中，不需要回表查询，可以显著提高查询速度。使用EXPLAIN查看执行计划时，Extra列显示Using index表示使用了覆盖索引。

索引失效的场景包括：在索引列上使用函数或表达式、LIKE查询以%开头、OR条件中部分列没有索引、隐式类型转换（如字符串与数字比较）、不等于操作符（!=或<>）。

## SQL查询优化

EXPLAIN是分析SQL执行计划的关键工具。重要字段包括：type（连接类型，system > const > eq_ref > ref > range > index > ALL）、key（使用的索引）、rows（扫描行数）、Extra（额外信息）。

优化建议：避免SELECT *只查询需要的字段；使用JOIN代替子查询；分页查询使用覆盖索引避免大偏移量；批量插入使用INSERT多值语法；适当使用缓存减少数据库压力。

分库分表策略：垂直分库按业务拆分，垂直分表按字段拆分，水平分表按数据行拆分。常用中间件包括ShardingSphere和MyCAT。

## 事务与锁

MySQL的InnoDB引擎支持事务，通过Redo Log保证持久性，Undo Log保证原子性。事务隔离级别包括：读未提交（脏读）、读已提交（不可重复读）、可重复读（幻读）、串行化。

锁的类型包括：共享锁（S锁，读锁）、排他锁（X锁，写锁）、意向锁（表级锁，表示后续将加行锁）、间隙锁（防止幻读）、临键锁（记录锁+间隙锁）。

死锁检测和处理：MySQL默认开启死锁检测（innodb_deadlock_detect），发生死锁时自动回滚代价较小的事务。可以通过show engine innodb status查看死锁信息。

## 慢查询优化

慢查询日志记录执行时间超过阈值的SQL。配置参数：slow_query_log（开启）、long_query_time（阈值秒）、slow_query_log_file（日志路径）。

优化工具：pt-query-digest分析慢查询日志，MySQL自带的Performance Schema监控运行时状态。常见优化方向：添加合适的索引、重写低效SQL、调整数据库参数配置。
""",
    )
    print(f"文档3: {doc3.name} - {len(doc3.chunks)} 个知识块")

    # ========== 文档4: 计算机网络==========
    doc4 = index_markdown_document(
        db,
        user_id="default-user",
        name="计算机网络核心知识",
        category="计算机网络",
        tags=["网络", "HTTP", "TCP/IP", "面试"],
        markdown_text="""# 计算机网络核心知识

## TCP/IP协议栈

TCP/IP协议分为四层：应用层、传输层、网络层、数据链路层。应用层协议包括HTTP、HTTPS、FTP、DNS、SMTP等。传输层负责端到端的通信，主要协议是TCP和UDP。网络层负责寻址和路由，核心协议是IP。网络接口层处理物理传输。

HTTP/1.1使用持久连接（Keep-Alive）复用TCP连接，但存在队头阻塞问题。HTTP/2通过多路复用解决队头阻塞，支持二进制分帧、头部压缩和服务器推送。HTTP/3基于QUIC协议（基于UDP），进一步减少了连接建立延迟。

TCP三次握手：客户端发送SYN -> 服务端回复SYN+ACK -> 客户端发送ACK。三次握手确保双方的发送和接收能力都正常。四次挥手：主动关闭方发送FIN -> 被动方回复ACK -> 被动方发送FIN -> 主动方回复ACK。

## TCP流量控制与拥塞控制

流量控制通过滑动窗口实现，接收方通过TCP头部的窗口大小字段告知发送方自己的接收能力。拥塞控制算法包括：慢启动（指数增长）、拥塞避免（线性增长）、快速重传（收到3个重复ACK立即重传）、快速恢复（阈值减半后线性增长）。

TCP状态机包含：LISTEN、SYN_SENT、SYN_RECEIVED、ESTABLISHED、FIN_WAIT_1、FIN_WAIT_2、CLOSE_WAIT、LAST_ACK、CLOSING、TIME_WAIT等状态。TIME_WAIT状态持续2MSL，确保被动关闭方收到最终的ACK。

## DNS解析过程

DNS（Domain Name System）将域名解析为IP地址。解析过程：客户端先查本地hosts文件 -> 本地DNS缓存 -> 操作系统DNS缓存 -> 本地域名服务器 -> 根域名服务器 -> 顶级域名服务器 -> 权威域名服务器。DNS支持递归查询和迭代查询。

DNS优化方法包括：使用CDN就近分配、DNS预解析（preconnect/dns-prefetch）、DNS缓存（TTL设置合理）、HTTPDNS避免域名劫持。

## HTTPS与TLS

HTTPS在HTTP和TCP之间加入了TLS/SSL层，提供加密、认证和完整性保护。TLS握手过程：客户端发送ClientHello（支持的加密套件）-> 服务端回复ServerHello（选定套件）+ 证书 -> 客户端验证证书并生成pre-master secret -> 双方生成会话密钥 -> 加密通信。

对称加密用于数据传输（如AES），非对称加密用于密钥交换（如RSA、ECDHE）。数字证书由CA机构签发，用于验证服务端身份。HTTPS性能优化包括：TLS Session Resumption减少握手开销、OCSP Stapling减少证书验证延迟、HTTP/2减少连接数。

## WebSocket

WebSocket提供全双工通信通道，建立在HTTP之上但协议不同（ws://）。握手通过HTTP Upgrade完成，之后切换到WebSocket协议。适用于实时聊天、股票行情、在线游戏等场景。
""",
    )
    print(f"文档4: {doc4.name} - {len(doc4.chunks)} 个知识块")

    # ========== 文档5: 设计模式==========
    doc5 = index_markdown_document(
        db,
        user_id="default-user",
        name="常见设计模式",
        category="设计模式",
        tags=["设计模式", "架构", "面试"],
        markdown_text="""# 常见设计模式

## 创建型模式

### 单例模式
确保一个类只有一个实例，并提供全局访问点。实现方式包括：饿汉式（类加载时创建）、懒汉式（首次使用时创建，双重检查锁定）、静态内部类方式（推荐，线程安全且延迟加载）、枚举方式（防止反射攻击）。单例模式适用于线程池、缓存、日志对象等需要全局唯一的场景。

### 工厂模式
简单工厂模式通过一个工厂类根据参数创建不同类型的对象。工厂方法模式定义创建对象的接口，由子类决定实例化哪个类。抽象工厂模式提供一个接口来创建相关或依赖对象的家族，而不需要指定具体类。工厂模式的核心思想是封装对象的创建逻辑，提高扩展性。

### 建造者模式
将一个复杂对象的构建与表示分离，使得同样的构建过程可以创建不同的表示。典型应用是StringBuilder。建造者模式适用于创建过程复杂、需要多个步骤组合的对象。

## 结构型模式

### 代理模式
为其他对象提供代理以控制访问。静态代理在编译期确定代理关系，动态代理在运行期通过反射创建。JDK动态代理基于接口，CGLIB基于字节码生成子类。Spring AOP底层就使用了动态代理。

### 适配器模式
将一个类的接口转换成客户端期望的另一个接口，使原本不兼容的类可以一起工作。Spring MVC中的HandlerAdapter就是适配器模式的应用。

### 装饰器模式
动态地给对象添加额外职责而不改变其结构。Java IO流中的BufferedReader对FileReader的包装就是典型的装饰器模式。

## 行为型模式

### 观察者模式
定义对象间的一对多依赖关系，当一个对象状态改变时，所有依赖者都会收到通知并自动更新。Java中的PropertyChangeListener和Spring的事件机制都使用了观察者模式。

### 策略模式
定义一系列算法，将每个算法封装起来，使它们可以互相替换。策略模式让算法的变化独立于使用算法的客户端。Spring中Bean的实例化策略、排序策略等都使用了策略模式。

### 模板方法模式
定义一个操作中的算法骨架，将某些步骤延迟到子类中实现。模板方法使得子类可以在不改变算法结构的情况下重定义特定步骤。Spring JdbcTemplate的query方法就是模板方法模式的经典应用。

### 责任链模式
将请求沿着处理者链传递，直到有处理者处理它。Spring Security的过滤器链、MyBatis的插件拦截器链都使用了责任链模式。每个处理器决定是否传递请求到下一个处理器。

## 模式选择原则

单一职责原则：一个类只负责一个功能领域。开放封闭原则：对扩展开放，对修改关闭。里氏替换原则：子类可以替换父类。依赖倒置原则：面向接口编程。接口隔离原则：使用多个专用接口而非一个通用接口。迪米特法则：最少知识原则，减少对象间的耦合。合成复用原则：优先使用组合而非继承。""",
    )
    print(f"文档5: {doc5.name} - {len(doc5.chunks)} 个知识块")

    # 统计
    print("\n--- 知识库概览 ---")
    print(f"  总文档数: 5")
    total_chunks = len(doc1.chunks) + len(doc2.chunks) + len(doc3.chunks) + len(doc4.chunks) + len(doc5.chunks)
    print(f"  总知识块数: {total_chunks}")
    print(f"  各文档: doc1={len(doc1.chunks)}, doc2={len(doc2.chunks)}, doc3={len(doc3.chunks)}, doc4={len(doc4.chunks)}, doc5={len(doc5.chunks)}")

    # 确保有技能状态（Java和数据库的）
    from app.config import generate_uuid
    for dim in ["Java", "数据库", "计算机网络", "设计模式"]:
        existing = db.query(UserSkillState).filter(
            UserSkillState.user_id == "default-user",
            UserSkillState.dimension == dim
        ).first()
        if not existing:
            state = UserSkillState(
                id=generate_uuid(),
                user_id="default-user",
                dimension=dim,
                level=2,
                confidence=60,
            )
            db.add(state)

    db.commit()
    db.close()
    print("\n知识库种子数据注入完成！")


if __name__ == "__main__":
    main()