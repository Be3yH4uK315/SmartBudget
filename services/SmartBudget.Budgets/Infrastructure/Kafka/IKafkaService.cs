using SmartBudget.Budgets.DTO;
namespace SmartBudget.Budgets.Infrastructure.Kafka
{
    /// <summary>
    /// Абстракция на сообщение в кафку.
    /// </summary>
    public interface IKafkaTopicProducer<T>
    {
        Task ProduceAsync(string key, T message, CancellationToken stoppingToken);
    }

    public interface IKafkaService
    {
        IKafkaTopicProducer<BudgetEventMessage> BudgetEvents { get; }
        IKafkaTopicConsumer<TransactionNewMessage> TransactionNew { get; }
        IKafkaTopicConsumer<TransactionUpdatedMessage> TransactionUpdated { get; }
    }
    /// <summary>
    /// Абстракция Kafka consumer
    /// </summary>
    public interface IKafkaTopicConsumer<T>
    {
        Task ConsumeAsync(Func<T, CancellationToken, Task> handler, CancellationToken stoppingToken);
    }
}