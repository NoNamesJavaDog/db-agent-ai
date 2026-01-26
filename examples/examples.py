"""
SQL Tuning AI Agent - Examples and Tests
示例和测试脚本
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_agent.core import SQLTuningAgent, DatabaseTools
from db_agent.llm import LLMClientFactory


def example_1_analyze_slow_query():
    """示例1: 分析单个慢查询"""
    print("\n" + "=" * 80)
    print("示例1: 分析单个慢查询")
    print("=" * 80 + "\n")

    # 配置
    api_key = os.getenv("ANTHROPIC_API_KEY", "your-api-key")
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "user": "postgres",
        "password": "password"
    }

    # 创建LLM客户端
    llm_client = LLMClientFactory.create(
        provider="claude",
        api_key=api_key
    )

    # 创建Agent
    agent = SQLTuningAgent(llm_client, db_config)

    # 用户问题
    user_message = """
    我有一个查询很慢,能帮我优化吗?

    SELECT * FROM orders
    WHERE user_id = 12345
    ORDER BY created_at DESC
    LIMIT 10;

    这个查询在生产环境要5秒才能返回结果。
    """

    print(f"用户: {user_message}\n")
    print("Agent思考中...\n")

    # Agent处理
    response = agent.chat(user_message)

    print(f"Agent:\n{response}\n")


def example_2_find_all_slow_queries():
    """示例2: 查找数据库中所有慢查询"""
    print("\n" + "=" * 80)
    print("示例2: 查找数据库中所有慢查询")
    print("=" * 80 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY", "your-api-key")
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "user": "postgres",
        "password": "password"
    }

    llm_client = LLMClientFactory.create(
        provider="claude",
        api_key=api_key
    )

    agent = SQLTuningAgent(llm_client, db_config)

    user_message = "帮我分析一下数据库中的慢查询,找出最影响性能的前5个。"

    print(f"用户: {user_message}\n")
    print("Agent思考中...\n")

    response = agent.chat(user_message)

    print(f"Agent:\n{response}\n")


def example_3_multi_turn_conversation():
    """示例3: 多轮对话"""
    print("\n" + "=" * 80)
    print("示例3: 多轮对话")
    print("=" * 80 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY", "your-api-key")
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "user": "postgres",
        "password": "password"
    }

    llm_client = LLMClientFactory.create(
        provider="claude",
        api_key=api_key
    )

    agent = SQLTuningAgent(llm_client, db_config)

    # 第一轮
    message1 = "帮我看看orders表的索引使用情况"
    print(f"用户: {message1}\n")
    response1 = agent.chat(message1)
    print(f"Agent: {response1}\n")
    print("-" * 80 + "\n")

    # 第二轮(Agent记得上下文)
    message2 = "你发现了哪些未使用的索引?"
    print(f"用户: {message2}\n")
    response2 = agent.chat(message2)
    print(f"Agent: {response2}\n")
    print("-" * 80 + "\n")

    # 第三轮
    message3 = "帮我删除那些未使用的索引"
    print(f"用户: {message3}\n")
    response3 = agent.chat(message3)
    print(f"Agent: {response3}\n")


def example_4_index_recommendation():
    """示例4: 索引推荐"""
    print("\n" + "=" * 80)
    print("示例4: 索引推荐")
    print("=" * 80 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY", "your-api-key")
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "user": "postgres",
        "password": "password"
    }

    llm_client = LLMClientFactory.create(
        provider="claude",
        api_key=api_key
    )

    agent = SQLTuningAgent(llm_client, db_config)

    user_message = """
    我的应用有以下常见查询:

    1. SELECT * FROM orders WHERE user_id = ? AND status = 'pending'
    2. SELECT * FROM orders WHERE created_at > ? ORDER BY created_at DESC
    3. SELECT COUNT(*) FROM orders WHERE user_id = ?

    请帮我设计合适的索引策略。
    """

    print(f"用户: {user_message}\n")
    print("Agent思考中...\n")

    response = agent.chat(user_message)

    print(f"Agent:\n{response}\n")


def example_5_explain_analysis():
    """示例5: EXPLAIN分析"""
    print("\n" + "=" * 80)
    print("示例5: EXPLAIN分析")
    print("=" * 80 + "\n")

    api_key = os.getenv("ANTHROPIC_API_KEY", "your-api-key")
    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "user": "postgres",
        "password": "password"
    }

    llm_client = LLMClientFactory.create(
        provider="claude",
        api_key=api_key
    )

    agent = SQLTuningAgent(llm_client, db_config)

    user_message = """
    帮我分析这个查询的EXPLAIN输出,告诉我性能瓶颈在哪:

    SELECT o.*, u.name
    FROM orders o
    JOIN users u ON o.user_id = u.id
    WHERE o.status = 'pending'
    ORDER BY o.created_at DESC
    LIMIT 100;
    """

    print(f"用户: {user_message}\n")
    print("Agent思考中...\n")

    response = agent.chat(user_message)

    print(f"Agent:\n{response}\n")


def test_database_tools():
    """测试数据库工具"""
    print("\n" + "=" * 80)
    print("测试数据库工具")
    print("=" * 80 + "\n")

    db_config = {
        "host": "localhost",
        "port": 5432,
        "database": "testdb",
        "user": "postgres",
        "password": "password"
    }

    tools = DatabaseTools(db_config)

    # 测试1: 安全查询
    print("测试1: 执行安全查询")
    result = tools.execute_safe_query("SELECT version();")
    print(f"结果: {result['status']}")
    if result['status'] == 'success':
        print(f"PostgreSQL版本: {result['rows'][0]}")
    print()

    # 测试2: 识别慢查询
    print("测试2: 识别慢查询")
    result = tools.identify_slow_queries(min_duration_ms=100, limit=5)
    print(f"结果: {result['status']}")
    if result['status'] == 'success':
        print(f"找到 {result['count']} 个慢查询")
    else:
        print(f"错误: {result.get('error')}")
    print()

    # 测试3: 运行EXPLAIN
    print("测试3: 运行EXPLAIN")
    result = tools.run_explain("SELECT 1;", analyze=False)
    print(f"结果: {result['status']}")
    if result['status'] == 'success':
        print("EXPLAIN执行成功")
    print()


def main():
    """运行所有示例"""
    print("\n" + "=" * 80)
    print("SQL Tuning AI Agent - 示例和测试")
    print("=" * 80)

    # 检查环境变量
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n  警告: 未设置ANTHROPIC_API_KEY环境变量")
        print("部分示例需要API Key才能运行\n")

    if not os.getenv("DB_NAME"):
        print("  警告: 未设置数据库配置环境变量")
        print("数据库相关示例可能失败\n")

    # 选择要运行的示例
    print("\n可用示例:")
    print("1. 分析单个慢查询")
    print("2. 查找数据库中所有慢查询")
    print("3. 多轮对话")
    print("4. 索引推荐")
    print("5. EXPLAIN分析")
    print("6. 测试数据库工具")
    print("0. 运行所有示例")

    choice = input("\n请选择要运行的示例 (0-6): ").strip()

    examples = {
        "1": example_1_analyze_slow_query,
        "2": example_2_find_all_slow_queries,
        "3": example_3_multi_turn_conversation,
        "4": example_4_index_recommendation,
        "5": example_5_explain_analysis,
        "6": test_database_tools
    }

    if choice == "0":
        for func in examples.values():
            try:
                func()
            except Exception as e:
                print(f"\n  示例执行失败: {e}\n")
    elif choice in examples:
        try:
            examples[choice]()
        except Exception as e:
            print(f"\n  示例执行失败: {e}\n")
    else:
        print("无效的选择")


if __name__ == "__main__":
    main()
