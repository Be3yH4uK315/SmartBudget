using Microsoft.AspNetCore.Mvc;
using System.Text.Json;
using SmartBudget.Transactions.Domain.DTO;
using SmartBudget.Transactions.Domain.Entities;
using SmartBudget.Transactions.Domain.Enums;
using SmartBudget.Transactions.Infrastructure.Kafka;
using SmartBudget.Transactions.Services;

using Microsoft.EntityFrameworkCore.Diagnostics;

namespace SmartBudget.Transactions.Controllers
{
    [ApiController]
    [Route("api/transactions")]
    public class TransactionsController : ControllerBase
    {
        private readonly ITransactionService _service;

        public TransactionsController(ITransactionService service)
        {
            _service = service;
        }

        /// <summary>
        /// GET Transactions in list
        /// </summary>
        [HttpGet]
        public async Task<IActionResult> List(
            [FromQuery(Name = "userId")] Guid UserId, 
            [FromQuery(Name = "limit")] int Limit = 50, 
            [FromQuery(Name = "offset")] int Offset = 0)
        {
            return Ok(await _service.GetUserTransactionsAsync(UserId, Limit, Offset));
        }


        /// <summary>
        /// GET single transaction
        /// </summary>
        [HttpGet("{id}")]
        public async Task<IActionResult> Get(Guid id)
        {
            var result = await _service.GetByTransactionIdAsync(id);
            return result == null ? NotFound() : Ok(result);
        }

        /// <summary>
        /// POST create manual transaction
        /// </summary>
        [HttpPost("manual")]
        public async Task<IActionResult> CreateManual([FromBody] CreateManualTransactionRequest _request)
        {
            return Ok(await _service.CreateManualTransactionAsync(_request));
        }

        /// <summary>
        /// POST import mocks
        /// </summary>
        [HttpPost("import/mock")]
        public async Task<IActionResult> ImportMock([FromBody] JsonElement body)
        {
            return Ok(await _service.ImportMockAsync(body));
        }

        /// <summary>
        /// PATCH: change category
        /// </summary>
        [HttpPatch("{id}")]
        public async Task<IActionResult> PatchCategory(Guid id, [FromBody] PatchTransactionCategoryRequest request)
        {
            return Ok(await _service.PatchCategoryAsync(id, request));
        }


        /// <summary>
        /// DELETE transaction
        /// </summary>
        [HttpDelete("{id}")]
        public async Task<IActionResult> Delete(Guid id)
        {
            await _service.DeleteAsync(id);
            return Ok();
        }
    }
}
