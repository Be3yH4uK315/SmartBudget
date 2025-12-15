using SmartBudget.Transactions.DTO;
namespace SmartBudget.Transactions.Infrastructure.Kafka
{
    /// <summary>
    /// Абстракция на сообщение в кафку.
    /// </summary>
    public interface IKafkaTopicProducer<T>
    {
        Task ProduceAsync(string key, T message, CancellationToken stoppingToken);
    }

    public interface IKafkaTopicConsumer<T>
    {
        Task ConsumeAsync(CancellationToken stoppingToken);
    }
    public interface IKafkaService
    {
        IKafkaTopicConsumer<TransactionClassifiedMessage> TransactionClassified { get; }
        IKafkaTopicProducer<TransactionNewMessage> TransactionNew { get; }
        IKafkaTopicProducer<TransactionImportedMessage> TransactionImported { get; }
        IKafkaTopicProducer<TransactionNeedCategoryMessage> TransactionNeedCategory { get; }
        IKafkaTopicProducer<TransactionUpdatedMessage> TransactionUpdated { get; }
        IKafkaTopicProducer<TransactionDeletedMessage> TransactionDeleted { get; }
        IKafkaTopicProducer<BudgetEventMessage> BudgetEvents { get; }
    }
}
