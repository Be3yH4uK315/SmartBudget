using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using System.Text.Json;
using System.Text.Json.Serialization;
using Confluent.Kafka;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace SmartBudget.Transactions
{
    public enum TxType { income, expense }
    public enum TxStatus { rejected, confirmed, pending }

    public class Transaction
    {
        [Key]
        public Guid Id { get; set; }

        [Required]
        public Guid UserId { get; set; }

        [MaxLength(200)]
        public string TransactionId { get; set;} 

        public Guid AccountId { get; set; }

        public int? CategoryId { get; set; }

        public DateTime? Date { get; set; }

        [Column(TypeName = "numeric(18,2)")]
        public decimal Value { get; set; }

        public TxType Type { get; set; }

        public TxStatus Status { get; set; }

        [MaxLength(500)]
        public string Merchant { get; set; }

        public int? Mcc { get; set; }

        [MaxLength(2000)]
        public string Description { get; set; }

        public DateTime? ImportedAt { get; set; }

        public DateTime? UpdatedAt { get; set; }
    }

    public class AppDbContext : DbContext
    {
        public DbSet<Transaction> Transactions { get; set; }

        public AppDbContext(DbContextOptions<AppDbContext> opts) : base(opts) { }

        protected override void OnModelCreating(ModelBuilder mb)
        {
            mb.Entity<Transaction>(b =>
            {
                b.ToTable("transactions");
                b.HasKey(x => x.Id);
                b.Property(x => x.TransactionId).HasMaxLength(200);
                b.Property(x => x.Merchant).HasMaxLength(500);
                b.Property(x => x.Description).HasMaxLength(2000);
                b.Property(x => x.Value).HasColumnType("numeric(18,2)");
            });
        }
    }

    // DTOs
    public class CreateManualTxRequest
    {
        [JsonPropertyName("USER_ID")] public string USER_ID { get; set; }
        [JsonPropertyName("ACCOUNT_ID")] public string ACCOUNT_ID { get; set; }
        [JsonPropertyName("VALUE")] public decimal VALUE { get; set; }
        [JsonPropertyName("CATEGORY_ID")] public int? CATEGORY_ID { get; set; }
        [JsonPropertyName("DESCRIPTION")] public string DESCRIPTION { get; set; }
        [JsonPropertyName("NAME")] public string NAME { get; set; }
    }

    public class ImportTxItem
    {
        [JsonPropertyName("id")] public string id { get; set; }
        [JsonPropertyName("user_id")] public string user_id { get; set; }
        [JsonPropertyName("transaction_id")] public string transaction_id { get; set; }
        [JsonPropertyName("account_id")] public string account_id { get; set; }
        [JsonPropertyName("date")] public string date { get; set; }
        [JsonPropertyName("Value")] public decimal? Value { get; set; } 
        [JsonPropertyName("type")] public string type { get; set; }
        [JsonPropertyName("status")] public string status { get; set; }
        [JsonPropertyName("merchant")] public string merchant { get; set; }
        [JsonPropertyName("mcc")] public int? mcc { get; set; }
        [JsonPropertyName("description")] public string description { get; set; }
    }

    public interface IKafkaService
    {
        Task ProduceAsync(string topic, string key, string message);
    }

    public class KafkaService : IKafkaService, IDisposable
    {
        private readonly IProducer<string, string> _producer;
        private readonly ILogger<KafkaService> _log;

        public KafkaService(IConfiguration cfg, ILogger<KafkaService> log)
        {
            _log = log;
            var conf = new ProducerConfig
            {
                BootstrapServers = cfg["KAFKA_BOOTSTRAP_SERVERS"] ?? "localhost:9092",
                // optional: set retries/acks etc
                Acks = Acks.All
            };
            _producer = new ProducerBuilder<string, string>(conf).Build();
        }

        public async Task ProduceAsync(string topic, string key, string message)
        {
            try
            {
                var r = await _producer.ProduceAsync(topic, new Message<string, string> { Key = key, Value = message });
                _log.LogInformation("Produced {topic} @{partition}/{offset}", topic, r.Partition, r.Offset);
            }
            catch (Exception ex)
            {
                _log.LogError(ex, "Kafka produce failed");
            }
        }

        public void Dispose() => _producer?.Dispose();
    }

    [ApiController]
    [Route("api/v1")]
    public class TransactionsController : ControllerBase
    {
        private readonly AppDbContext _db;
        private readonly IKafkaService _kafka;
        private readonly ILogger<TransactionsController> _log;

        public TransactionsController(AppDbContext db, IKafkaService kafka, ILogger<TransactionsController> log)
        {
            _db = db; _kafka = kafka; _log = log;
        }

        //GET Transactions in list
        [HttpGet("transactions")]
        public async Task<IActionResult> List([FromQuery] string USER_ID, [FromQuery] int LIMIT = 50, [FromQuery] int OFFSET = 0)
        {
            if (!Guid.TryParse(USER_ID, out var uid)) return BadRequest("Invalid USER_ID");
            var q = _db.Transactions.Where(t => t.UserId == uid)
                                    .OrderByDescending(t => t.Date)
                                    .Skip(OFFSET).Take(LIMIT);
            var list = await q.ToListAsync();
            return Ok(list.Select(t => new {
                TRANSACTION_ID = t.TransactionId,
                VALUE = t.Value,
                CATEGORY_ID = t.CategoryId,
                DESCRIPTION = t.Description,
                NAME = t.Merchant,
                MCC = t.Mcc,
                STATUS = t.Status.ToString(),
                DATE = t.Date?.ToString("o")
            }));
        }

        // GET single transaction
        [HttpGet("transactions/{id}")]
        public async Task<IActionResult> Get(string id)
        {
            var tx = await _db.Transactions.FirstOrDefaultAsync(t => t.TransactionId == id);
            if (tx == null) return NotFound();
            return Ok(tx);
        }

        // POST create manual transaction
        [HttpPost("transactions/manual")]
        public async Task<IActionResult> CreateManual([FromBody] CreateManualTxRequest req)
        {
            if (!Guid.TryParse(req.USER_ID, out var uid)) return BadRequest("USER_ID invalid");
            if (!Guid.TryParse(req.ACCOUNT_ID, out var aid)) return BadRequest("ACCOUNT_ID invalid");

            var tx = new Transaction
            {
                Id = Guid.NewGuid(),
                UserId = uid,
                TransactionId = "MANUAL-" + Guid.NewGuid(),
                AccountId = aid,
                Value = req.VALUE,
                Type = req.VALUE >= 0 ? TxType.income : TxType.expense,
                Status = TxStatus.confirmed,
                Merchant = req.NAME,
                Description = req.DESCRIPTION,
                ImportedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow,
                CategoryId = req.CATEGORY_ID
            };

            _db.Transactions.Add(tx);
            await _db.SaveChangesAsync();

            var simple = JsonSerializer.Serialize(new { ACCOUNT_ID = tx.AccountId, CATEGORY_ID = tx.CategoryId, VALUE = tx.Value });
            await _kafka.ProduceAsync("transaction.new", tx.TransactionId, simple);

            var evt = JsonSerializer.Serialize(new { event_type = "transaction.new", user_id = tx.UserId, details = tx });
            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, evt);

            return Ok(new { TRANSACTION_ID = tx.TransactionId });
        }

        // POST import/mock - accept array or single object in the same shape as ImportTxItem
        [HttpPost("transactions/import/mock")]
        public async Task<IActionResult> ImportMock([FromBody] JsonElement body)
        {
            List<ImportTxItem> items = new();
            if (body.ValueKind == JsonValueKind.Array)
            {
                items = JsonSerializer.Deserialize<List<ImportTxItem>>(body.GetRawText());
            }
            else if (body.ValueKind == JsonValueKind.Object)
            {
                var single = JsonSerializer.Deserialize<ImportTxItem>(body.GetRawText());
                items.Add(single);
            }
            else return BadRequest("Invalid body");

            var created = new List<object>();

            foreach (var it in items)
            {
                try
                {
                    var tx = new Transaction
                    {
                        Id = Guid.TryParse(it.id, out var gid) ? gid : Guid.NewGuid(),
                        UserId = Guid.TryParse(it.user_id, out var uid) ? uid : Guid.Empty,
                        TransactionId = it.transaction_id ?? Guid.NewGuid().ToString(),
                        AccountId = Guid.TryParse(it.account_id, out var aid) ? aid : Guid.Empty,
                        Date = DateTime.TryParse(it.date, out var d) ? d : (DateTime?)null,
                        Value = it.Value ?? 0m,
                        Type = Enum.TryParse<TxType>(it.type ?? "expense", true, out var tt) ? tt : TxType.expense,
                        Status = Enum.TryParse<TxStatus>(it.status ?? "pending", true, out var st) ? st : TxStatus.pending,
                        Merchant = it.merchant,
                        Mcc = it.mcc,
                        Description = it.description,
                        ImportedAt = DateTime.UtcNow,
                        UpdatedAt = DateTime.UtcNow,
                        CategoryId = null
                    };

                    if (tx.UserId == Guid.Empty) continue;

                    var exists = await _db.Transactions.AnyAsync(t => t.TransactionId == tx.TransactionId);
                    if (!exists)
                    {
                        _db.Transactions.Add(tx);
                        await _db.SaveChangesAsync();

                        var importedPayload = JsonSerializer.Serialize(new { event_type = "transaction.imported", user_id = tx.UserId, details = tx });
                        await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, importedPayload);

                        var need = JsonSerializer.Serialize(new { TRANSACTION_ID = tx.TransactionId, ACCOUNT_ID = tx.AccountId, MERCHANT = tx.Merchant, MCC = tx.Mcc, Description = tx.Description });
                        await _kafka.ProduceAsync("transaction.need_category", tx.TransactionId, need);

                        created.Add(new { tx.TransactionId });
                    }
                }
                catch (Exception ex)
                {
                    _log.LogError(ex, "Import mock item failed");
                }
            }

            return Ok(new { created_count = created.Count, created });
        }

        // PATCH: change category of a transaction
        [HttpPatch("transactions/{id}")]
        public async Task<IActionResult> PatchCategory(string id, [FromBody] JsonElement body)
        {
            int? newCat = null;
            if (body.TryGetProperty("CATEGORY_ID", out var catEl))
            {
                if (catEl.ValueKind == JsonValueKind.Number && catEl.TryGetInt32(out var v)) newCat = v;
                else if (catEl.ValueKind == JsonValueKind.Null) newCat = null;
                else return BadRequest("CATEGORY_ID must be integer or null");
            }
            else return BadRequest("CATEGORY_ID required");

            var tx = await _db.Transactions.FirstOrDefaultAsync(t => t.TransactionId == id);
            if (tx == null) return NotFound();

            var old = tx.CategoryId;
            tx.CategoryId = newCat;
            tx.UpdatedAt = DateTime.UtcNow;
            await _db.SaveChangesAsync();

            var upd = JsonSerializer.Serialize(new { event_type = "transaction.updated", user_id = tx.UserId, details = new { TRANSACTION_ID = tx.TransactionId, OLD_CATEGORY = old, NEW_CATEGORY = newCat } });
            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, upd);

            var simple = JsonSerializer.Serialize(new { TRANSACTION_ID = tx.TransactionId, OLD_CATEGORY = old, NEW_CATEGORY = newCat });
            await _kafka.ProduceAsync("transaction.updated", tx.TransactionId, simple);

            return Ok("OK");
        }

        // DELETE transaction
        [HttpDelete("transactions/{id}")]
        public async Task<IActionResult> Delete(string id)
        {
            var tx = await _db.Transactions.FirstOrDefaultAsync(t => t.TransactionId == id);
            if (tx == null) return NotFound();
            _db.Transactions.Remove(tx);
            await _db.SaveChangesAsync();

            await _kafka.ProduceAsync("budget.transactions.events", tx.TransactionId, JsonSerializer.Serialize(new { event_type = "transaction.deleted", user_id = tx.UserId, details = new { TRANSACTION_ID = tx.TransactionId } }));

            return Ok("OK");
        }

    }

    public class Program
    {
        public static void Main(string[] args)
        {
            var b = WebApplication.CreateBuilder(args);
            var services = b.Services;
            var cfg = b.Configuration;

            services.AddControllers().AddJsonOptions(o =>
            {
                o.JsonSerializerOptions.PropertyNamingPolicy = null;
            });
            services.AddEndpointsApiExplorer();
            services.AddSwaggerGen();

            var pg = cfg["DATABASE_DSN"] ?? "Host=postgres;Database=smartbudget;Username=postgres;Password=postgres";
            services.AddDbContext<AppDbContext>(opt => opt.UseNpgsql(pg));

            services.AddSingleton<IKafkaService, KafkaService>();

            var app = b.Build();

            using (var scope = app.Services.CreateScope())
            {
                var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();
                var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
                var retries = 10;
                while (retries-- > 0)
                {
                    try
                    {
                        db.Database.Migrate();
                        break;
                    }
                    catch (Exception ex)
                    {
                        logger.LogWarning("Database not ready yet: {m}", ex.Message);
                        if (retries == 0) throw;
                        Thread.Sleep(2000);
                    }
                }
            }

            if (app.Environment.IsDevelopment())
            {
                app.UseSwagger();
                app.UseSwaggerUI();
            }

            app.MapControllers();

            var url = Environment.GetEnvironmentVariable("ASPNETCORE_URLS") ?? "http://+:8082";
            app.Urls.Clear();
            app.Urls.Add(url);

            app.Run();
        }
    }
}
