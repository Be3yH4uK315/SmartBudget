using Microsoft.EntityFrameworkCore;
using SmartBudget.Transactions.Data;
using SmartBudget.Transactions.Infrastructure.Kafka;
using System.Reflection;

var builder = WebApplication.CreateBuilder(args);

// Controllers
builder.Services.AddControllers()
    .AddJsonOptions(o =>
    {
        o.JsonSerializerOptions.PropertyNamingPolicy = null; // keep JSON names from DTO
    });

// DB
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("Default")));

// Kafka
builder.Services.AddSingleton<IKafkaService, KafkaService>();

// Swagger
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    var xml = $"{Assembly.GetExecutingAssembly().GetName().Name}.xml";
    var xmlPath = Path.Combine(AppContext.BaseDirectory, xml);
    c.IncludeXmlComments(xmlPath, includeControllerXmlComments: true);
});

var app = builder.Build();

app.UseSwagger();
app.UseSwaggerUI();

// Routing
app.MapControllers();

app.Run();
