using System.Text.Json;
using Microsoft.EntityFrameworkCore;
using SmartBudget.Transactions.Data;
using SmartBudget.Transactions.DTO;
using SmartBudget.Transactions.Domain.Entities;
using SmartBudget.Transactions.Domain.Enums;
using SmartBudget.Transactions.Infrastructure.Kafka;
using Microsoft.AspNetCore.Http.HttpResults;

namespace SmartBudget.Transactions.Services
{
    public class TransactionService : ITransactionService
    {
        private readonly AppDbContext _db;
        private readonly IKafkaService _kafka;
        private readonly ILogger<TransactionService> _log;

        public TransactionService(AppDbContext db, IKafkaService kafka, ILogger<TransactionService> log)
        {
            _db = db;
            _kafka = kafka;
            _log = log;
        }

        public async Task<List<Transaction>> GetUserTransactionsAsync(Guid userId, int limit, int offset, int category_id, CancellationToken stoppingToken)
        {
            return await _db.Transactions
                .Where(new_transaction => new_transaction.UserId == userId && (category_id == 0 || new_transaction.CategoryId == category_id))
                .OrderByDescending(new_transaction => new_transaction.CreatedAt)
                .Skip(offset)
                .Take(limit)
                .ToListAsync(stoppingToken);
        }


        public async Task<Transaction?> GetByTransactionIdAsync(Guid transactionId, CancellationToken stoppingToken)
        {
            return await _db.Transactions.FirstOrDefaultAsync(new_transaction => new_transaction.TransactionId == transactionId, stoppingToken);
        }


        public async Task<string> CreateManualTransactionAsync(Transaction transaction, CancellationToken stoppingToken)
        {
            using var transactionBD = await _db.Database.BeginTransactionAsync(stoppingToken);
            try
            {
                _db.Transactions.Add(transaction);
                await _db.SaveChangesAsync(stoppingToken);

                await _kafka.TransactionNew.ProduceAsync(transaction.TransactionId.ToString(), new TransactionNewMessage(transaction.UserId, transaction.CategoryId, transaction.Value, transaction.Type), stoppingToken);

                await _kafka.BudgetEvents.ProduceAsync(transaction.TransactionId.ToString(), new BudgetEventMessage("transaction.new", transaction.UserId, transaction), stoppingToken);
                if (transaction.CategoryId == 24)
                {
                    await _kafka.TransactionNewGoal.ProduceAsync(transaction.TransactionId.ToString(), new TransactionNewGoalMessage(transaction.TransactionId, transaction.AccountId, transaction.UserId, transaction.Value, transaction.Type), stoppingToken);
                }
                await transactionBD.CommitAsync(stoppingToken);
            }
            catch (Exception except)
            {
                await transactionBD.RollbackAsync(stoppingToken);
                _log.LogError(except, "Creating transaction failed");
            }

            return transaction.TransactionId.ToString();
        }



        public async Task<int> ImportMockAsync(List<Transaction> transactions, CancellationToken stoppingToken)
        {
            int count = 0;
            foreach (var current_transaction in transactions)
            {
                if (current_transaction.AccountId != Guid.Empty)
                {
                    current_transaction.CategoryId = 24;
                    current_transaction.Description = current_transaction.Type switch
                    {
                        TransactionType.income => "Пополнение цели",
                        TransactionType.expense => "Списание с цели",
                        _ => current_transaction.Description
                    };
                }
                using var transactionBD = await _db.Database.BeginTransactionAsync(stoppingToken);
                try
                {
                    if (!await _db.Transactions.AnyAsync(x => x.TransactionId == current_transaction.TransactionId, stoppingToken))
                    {
                        _db.Transactions.Add(current_transaction);
                        await _db.SaveChangesAsync(stoppingToken);

                        await _kafka.TransactionImported.ProduceAsync(current_transaction.TransactionId.ToString(), new TransactionImportedMessage("transaction.imported", current_transaction.UserId, current_transaction), stoppingToken);

                        if (current_transaction.CategoryId == 24)
                        {
                            await _kafka.TransactionNew.ProduceAsync(current_transaction.TransactionId.ToString(), new TransactionNewMessage(current_transaction.UserId, current_transaction.CategoryId, current_transaction.Value, current_transaction.Type), stoppingToken);

                            await _kafka.TransactionNewGoal.ProduceAsync(current_transaction.TransactionId.ToString(), new TransactionNewGoalMessage(current_transaction.TransactionId, current_transaction.AccountId, current_transaction.UserId, current_transaction.Value, current_transaction.Type), stoppingToken);
                        }
                        else
                        {
                            await _kafka.TransactionNeedCategory.ProduceAsync(current_transaction.TransactionId.ToString(), new TransactionNeedCategoryMessage(current_transaction.TransactionId, current_transaction.AccountId, current_transaction.Merchant, current_transaction.Mcc, current_transaction.Description), stoppingToken);
                        }


                        await transactionBD.CommitAsync(stoppingToken);
                        count++;
                    }
                }
                catch (Exception except)
                {
                    await transactionBD.RollbackAsync();
                    _log.LogError(except, "Import mock failed");
                }
            }

            return count;
        }

        public async Task<string> PatchCategoryAsync(Guid Id, PatchTransactionCategoryRequest request, CancellationToken stoppingToken)
        {
            var transaction = await _db.Transactions.FirstOrDefaultAsync(new_transaction => new_transaction.TransactionId == Id);
            if (transaction == null) throw new Exception("Not found");

            var old = transaction.CategoryId;
            transaction.CategoryId = request.CategoryId;
            transaction.UpdatedAt = DateTime.UtcNow;

            await _db.SaveChangesAsync();

            await _kafka.TransactionUpdated.ProduceAsync(transaction.TransactionId.ToString(), new TransactionUpdatedMessage(transaction.TransactionId, old, request.CategoryId, transaction.Value, transaction.Type), stoppingToken);

            await _kafka.BudgetEvents.ProduceAsync(transaction.TransactionId.ToString(), new BudgetEventMessage("transaction.updated", transaction.UserId, new { transaction.TransactionId, OldCategoryId = old, NewCategoryId = request.CategoryId }), stoppingToken);

            return "OK";
        }

        public async Task DeleteAsync(Guid Id, CancellationToken stoppingToken)
        {
            var transaction = await _db.Transactions.FirstOrDefaultAsync(new_transaction => new_transaction.TransactionId == Id);
            if (transaction == null) return;
            using var transactionBD = await _db.Database.BeginTransactionAsync();
            try
            {
                _db.Transactions.Remove(transaction);
                await _db.SaveChangesAsync();

                await _kafka.TransactionDeleted.ProduceAsync(transaction.TransactionId.ToString(), new TransactionDeletedMessage(transaction.TransactionId, transaction.UserId), stoppingToken);

                await _kafka.BudgetEvents.ProduceAsync(transaction.TransactionId.ToString(), new BudgetEventMessage("transaction.deleted", transaction.UserId, new { transaction.TransactionId }), stoppingToken);

                await transactionBD.CommitAsync();

            }
            catch (Exception except)
            {
                await transactionBD.RollbackAsync();
                _log.LogError(except, "Deleting transaction failed");
            }
        }

        public async Task<List<TransactionsByMonth>> GetUserTransactionsGoalsAsync(Guid accountId, CancellationToken stoppingToken)
        {
            return await _db.Transactions
        .Where(t => t.AccountId == accountId)
        .GroupBy(t => new
        {
            t.CreatedAt.Year,
            t.CreatedAt.Month,
            t.Type
        })
        .Select(g => new TransactionsByMonth
        {
            Value = g.Sum(x => x.Value),

            Date = new DateTime(
                g.Key.Year,
                g.Key.Month,
                1,
                0, 0, 0,
                DateTimeKind.Utc),

            Type = g.Key.Type
        })
        .OrderByDescending(x => x.Date)
        .ThenBy(x => x.Type)
        .ToListAsync(stoppingToken);

        }
    }

}

