using SmartBudget.Transactions.DTO;
namespace SmartBudget.Transactions.Infrastructure.Kafka
{
/// <summary>
/// Абстракция на сообщение в кафку.
/// </summary>
public interface IKafkaTopicProducer<T>
{
    Task ProduceAsync(object key, T message);
}

public interface IKafkaService
{
    IKafkaTopicProducer<TransactionNewMessage> TransactionNew { get; }
    IKafkaTopicProducer<TransactionImportedMessage> TransactionImported { get; }
    IKafkaTopicProducer<TransactionNeedCategoryMessage> TransactionNeedCategory { get; }
    IKafkaTopicProducer<TransactionUpdatedMessage> TransactionUpdated { get; }
    IKafkaTopicProducer<TransactionDeletedMessage> TransactionDeleted { get; }
    IKafkaTopicProducer<BudgetEventMessage> BudgetEvents { get; }
}
}
