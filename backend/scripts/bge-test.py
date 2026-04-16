import requests
import json
import numpy as np
import sys
import io
from typing import Optional
from dataclasses import dataclass, field

# Fix Windows GBK encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

@dataclass
class TestConfig:
    """测试配置类"""
    api_url: str = "http://localhost:8000/v1/embeddings"
    health_url: str = "http://localhost:8000/health"
    models_url: str = "http://localhost:8000/v1/models"
    version_url: str = "http://localhost:8000/version"
    model_name: str = "BAAI/bge-m3"
    timeout: int = 30
    
    # 相似度阈值配置
    similarity_threshold_high: float = 0.7
    similarity_threshold_medium: float = 0.5
    
    # 批量测试配置
    batch_size: int = 10
    
    # 统计信息
    stats: dict = field(default_factory=lambda: {
        'total_tests': 0,
        'passed_tests': 0,
        'failed_tests': 0
    })

config = TestConfig()


def print_section(title: str):
    """打印分隔线和标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success: bool, message: str, details: Optional[str] = None):
    """打印测试结果"""
    icon = "✅" if success else "❌"
    status = "PASS" if success else "FAIL"
    print(f"{icon} [{status}] {message}")
    if details:
        print(f"     {details}")
    
    config.stats['total_tests'] += 1
    if success:
        config.stats['passed_tests'] += 1
    else:
        config.stats['failed_tests'] += 1


def check_server_status():
    """检查服务器状态"""
    print_section("🏥 服务器状态检查")
    
    try:
        # 检查健康端点
        health_response = requests.get(config.health_url, timeout=config.timeout)
        if health_response.status_code == 200:
            print_result(True, "健康检查通过", f"状态码: {health_response.status_code}")
        else:
            print_result(False, "健康检查失败", f"状态码: {health_response.status_code}")
            return False
        
        # 检查模型端点
        try:
            models_response = requests.get(config.models_url, timeout=config.timeout)
            if models_response.status_code == 200:
                models_data = models_response.json()
                if 'data' in models_data and len(models_data['data']) > 0:
                    model_id = models_data['data'][0]['id']
                    print_result(True, "模型列表获取成功", f"可用模型: {model_id}")
                else:
                    print_result(False, "模型列表为空")
            else:
                print_result(False, "模型列表获取失败", f"状态码: {models_response.status_code}")
        except Exception as e:
            print_result(False, "模型列表检查异常", str(e))
        
        # 检查版本
        try:
            version_response = requests.get(config.version_url, timeout=config.timeout)
            if version_response.status_code == 200:
                print_result(True, "版本信息获取成功", f"版本: {version_response.text.strip()}")
            else:
                print_result(False, "版本信息获取失败", f"状态码: {version_response.status_code}")
        except Exception as e:
            print_result(False, "版本检查异常", str(e))
            
        return True
            
    except Exception as e:
        print_result(False, "服务器连接失败", f"错误: {e}")
        print("\n⚠️  请确保 BGE-M3 服务已启动并运行在 http://localhost:8000")
        return False


def test_basic_embedding():
    """测试基本文本嵌入"""
    print_section("📝 基本嵌入测试")
    
    headers = {"Content-Type": "application/json"}
    
    # 测试数据 - 包含求职相关场景
    texts = [
        "深度学习是人工智能的一个重要分支",
        "自然语言处理让计算机理解人类语言",
        "文本嵌入模型可以将文本转换为向量表示",
        "我在面试中展示了Python编程能力",
        "具备机器学习和数据分析经验"
    ]
    
    payload = {
        "model": config.model_name,
        "input": texts
    }
    
    try:
        response = requests.post(
            config.api_url, 
            headers=headers, 
            json=payload,
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # 验证返回结构
            if 'data' not in result:
                print_result(False, "响应格式错误", "缺少 'data' 字段")
                return None
            
            vector_count = len(result['data'])
            if vector_count != len(texts):
                print_result(False, "向量数量不匹配", f"期望: {len(texts)}, 实际: {vector_count}")
                return None
            
            print_result(True, "嵌入测试成功", f"返回 {vector_count} 个向量")
            
            # 验证向量维度
            first_embedding = result['data'][0]['embedding']
            dimension = len(first_embedding)
            print_result(True, "向量维度正常", f"维度: {dimension}")
            
            # 显示第一个向量的统计信息
            vec_array = np.array(first_embedding)
            print(f"\n📊 第一个向量统计信息:")
            print(f"   - 均值: {np.mean(vec_array):.6f}")
            print(f"   - 标准差: {np.std(vec_array):.6f}")
            print(f"   - 最小值: {np.min(vec_array):.6f}")
            print(f"   - 最大值: {np.max(vec_array):.6f}")
            print(f"   - L2范数: {np.linalg.norm(vec_array):.6f}")
            
            # 验证是否归一化（L2范数应接近1）
            is_normalized = abs(np.linalg.norm(vec_array) - 1.0) < 0.001
            print_result(is_normalized, "向量归一化检查", f"L2范数: {np.linalg.norm(vec_array):.6f}")
            
            return result
        else:
            print_result(False, "请求失败", f"状态码: {response.status_code}, 错误: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        print_result(False, "请求超时", f"超过 {config.timeout} 秒")
        return None
    except Exception as e:
        print_result(False, "连接错误", str(e))
        return None


def get_embedding(text: str) -> Optional[list[float]]:
    """获取单个文本的嵌入向量"""
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": config.model_name,
        "input": text
    }
    
    try:
        response = requests.post(
            config.api_url, 
            headers=headers, 
            json=payload,
            timeout=config.timeout
        )
        if response.status_code == 200:
            return response.json()['data'][0]['embedding']
        else:
            print_result(False, f"获取嵌入失败: {text[:30]}...", f"状态码: {response.status_code}")
            return None
    except Exception as e:
        print_result(False, f"获取嵌入异常: {text[:30]}...", str(e))
        return None


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """计算余弦相似度"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def test_similarity():
    """测试语义相似度"""
    print_section("🔍 语义相似度测试")
    
    # 测试用例：[(文本A, 文本B, 预期关系), ...]
    test_pairs = [
        # 高相似度 - 求职相关
        ("深度学习是人工智能的核心技术", "神经网络可以从数据中自动学习特征", "high"),
        ("如何提高英语口语能力", "练好英语口语的方法有哪些", "high"),
        ("具备Python编程和数据分析能力", "熟练掌握Python及数据处理技能", "high"),
        ("面试中展示了项目管理经验", "具有带领团队完成项目的经历", "high"),
        
        # 低相似度
        ("我喜欢吃苹果", "今天天气很好", "low"),
        ("深度学习是人工智能的核心技术", "今天股市行情不错", "low"),
        ("Python编程入门", "烤箱做蛋糕的食谱", "low"),
        ("机器学习算法优化", "如何做红烧肉", "low"),
        
        # 中等相似度
        ("人工智能的发展", "机器学习算法优化技巧", "medium"),
        ("北京是中国的首都", "上海有很多高楼大厦", "medium"),
        ("软件开发工程师", "前端开发岗位要求", "medium"),
    ]
    
    print(f"\n测试 {len(test_pairs)} 组文本对...\n")
    
    results = []
    for idx, (text_a, text_b, expected) in enumerate(test_pairs, 1):
        emb_a = get_embedding(text_a)
        emb_b = get_embedding(text_b)
        
        if emb_a and emb_b:
            score = cosine_similarity(emb_a, emb_b)
            
            # 判断实际相似度等级
            if score >= config.similarity_threshold_high:
                actual = "high"
            elif score >= config.similarity_threshold_medium:
                actual = "medium"
            else:
                actual = "low"
            
            match = actual == expected
            icon = "✅" if match else "⚠️"
            
            results.append({
                'idx': idx,
                'score': score,
                'expected': expected,
                'actual': actual,
                'match': match,
                'text_a': text_a,
                'text_b': text_b
            })
            
            print(f"{icon} [{idx:2d}] 预期:{expected:6s} | 实际:{actual:6s} | 得分:{score:.4f}")
            print(f"       A: {text_a[:40]}")
            print(f"       B: {text_b[:40]}")
    
    # 统计准确率
    correct = sum(1 for r in results if r['match'])
    total = len(results)
    accuracy = (correct / total * 100) if total > 0 else 0
    
    print("-" * 60)
    print_result(correct == total, f"相似度测试准确率", f"{correct}/{total} ({accuracy:.1f}%)")
    
    if accuracy < 80:
        print("\n⚠️  警告: 准确率较低，可能需要调整相似度阈值")
        print(f"   当前阈值: high>={config.similarity_threshold_high}, medium>={config.similarity_threshold_medium}")
    
    return results


def test_multilingual():
    """测试多语言支持（BGE-M3支持多语言）"""
    print_section("🌍 多语言支持测试")
    
    multilingual_texts = [
        ("Hello, how are you?", "英语"),
        ("Bonjour, comment allez-vous?", "法语"),
        ("你好，最近怎么样？", "中文"),
        ("Hola, ¿cómo estás?", "西班牙语"),
        ("こんにちは、お元気ですか？", "日语"),
        ("안녕하세요, 어떻게 지내세요?", "韩语"),
    ]
    
    embeddings = []
    for text, lang in multilingual_texts:
        emb = get_embedding(text)
        if emb:
            embeddings.append((text, lang, emb))
            print_result(True, f"{lang}文本嵌入成功", f"'{text}'")
        else:
            print_result(False, f"{lang}文本嵌入失败", f"'{text}'")
    
    # 测试跨语言相似度（中英文相同含义）
    if len(embeddings) >= 2:
        print("\n📊 跨语言相似度测试:")
        chinese_emb = next((emb for text, lang, emb in embeddings if lang == "中文"), None)
        english_emb = next((emb for text, lang, emb in embeddings if lang == "英语"), None)
        
        if chinese_emb and english_emb:
            score = cosine_similarity(chinese_emb, english_emb)
            print(f"   中文-英文问候语相似度: {score:.4f}")
            print_result(score > 0.5, "跨语言语义对齐", f"相似度: {score:.4f}")
    
    return len(embeddings) == len(multilingual_texts)


def test_batch_processing():
    """测试批量处理能力"""
    print_section("⚡ 批量处理性能测试")
    
    # 生成测试文本 - 使用求职场景相关文本
    batch_texts = [
        f"这是第{i}个测试文本，用于测试BGE-M3模型的批量处理能力，包含求职相关的专业术语和技能描述。" 
        for i in range(config.batch_size)
    ]
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": config.model_name,
        "input": batch_texts
    }
    
    try:
        import time
        start_time = time.time()
        
        response = requests.post(
            config.api_url, 
            headers=headers, 
            json=payload,
            timeout=config.timeout * 2  # 批量处理允许更长时间
        )
        
        elapsed_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            vector_count = len(result['data'])
            
            print_result(True, "批量处理成功", f"处理 {vector_count} 个文本")
            print(f"\n📊 性能指标:")
            print(f"   - 总耗时: {elapsed_time:.2f}秒")
            print(f"   - 平均每个文本: {elapsed_time/config.batch_size:.3f}秒")
            print(f"   - 吞吐量: {config.batch_size/elapsed_time:.2f} 文本/秒")
            
            # 评估性能
            avg_time = elapsed_time / config.batch_size
            if avg_time < 0.5:
                print_result(True, "性能优秀", f"平均 {avg_time:.3f}秒/文本")
            elif avg_time < 1.0:
                print_result(True, "性能良好", f"平均 {avg_time:.3f}秒/文本")
            else:
                print_result(False, "性能需优化", f"平均 {avg_time:.3f}秒/文本")
            
            return True
        else:
            print_result(False, "批量处理失败", f"状态码: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print_result(False, "批量处理超时", f"超过 {config.timeout * 2} 秒")
        return False
    except Exception as e:
        print_result(False, "批量处理异常", str(e))
        return False


def test_edge_cases():
    """测试边界情况"""
    print_section("🔬 边界情况测试")
    
    edge_cases = [
        ("空字符串", ""),
        ("单个字符", "a"),
        ("超长文本", "这是一个非常长的测试文本。" * 100),
        ("特殊字符", "!@#$%^&*()_+-=[]{}|;':\",./<>?"),
        ("纯数字", "123456789"),
        ("emoji表情", "😀😃😄😁😆😅🤣😂🙂🙃😉😊😇"),
    ]
    
    results = []
    for name, text in edge_cases:
        emb = get_embedding(text)
        if emb:
            dimension = len(emb)
            print_result(True, f"{name}处理成功", f"维度: {dimension}")
            results.append(True)
        else:
            print_result(False, f"{name}处理失败")
            results.append(False)
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📊 边界情况通过率: {success_rate:.1f}%")
    return success_rate > 80


def print_summary():
    """打印测试总结"""
    print_section("📊 测试总结")
    
    stats = config.stats
    total = stats['total_tests']
    passed = stats['passed_tests']
    failed = stats['failed_tests']
    
    print(f"\n总测试数: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"\n成功率: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("\n🎉 测试结果优秀！BGE-M3 模型运行正常")
        elif success_rate >= 70:
            print("\n✨ 测试结果良好，部分功能需要关注")
        else:
            print("\n⚠️  测试结果不理想，请检查服务和配置")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    print("=" * 60)
    print("  BGE-M3 文本嵌入模型完整测试套件")
    print("=" * 60)
    print(f"\n配置信息:")
    print(f"  API地址: {config.api_url}")
    print(f"  模型名称: {config.model_name}")
    print(f"  超时时间: {config.timeout}秒")
    print(f"  相似度阈值: high>={config.similarity_threshold_high}, medium>={config.similarity_threshold_medium}")
    
    # 1. 检查服务器状态
    server_ok = check_server_status()
    if not server_ok:
        print("\n❌ 服务器未就绪，终止测试")
        sys.exit(1)
    
    # 2. 基本嵌入测试
    basic_result = test_basic_embedding()
    if not basic_result:
        print("\n⚠️  基本嵌入测试失败，继续其他测试...")
    
    # 3. 语义相似度测试
    similarity_results = test_similarity()
    
    # 4. 多语言测试
    multilingual_ok = test_multilingual()
    
    # 5. 批量处理测试
    batch_ok = test_batch_processing()
    
    # 6. 边界情况测试
    edge_ok = test_edge_cases()
    
    # 7. 打印总结
    print_summary()
    
    print("\n测试完成！")
