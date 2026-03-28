---
name: napos-shopinfo
description: |
  餐饮门店基础信息查询工具，通过直接调用 HTTP 接口获取门店详细信息，包括门店基本属性、业务属性、营业时间、标签属性、类目信息、品牌信息及扩展属性。当用户需要查询门店信息、门店详情、门店资料、门店基础数据时使用。
version: 0.1.0
---

# 门店信息查询

查询餐饮门店的完整基础信息，包括门店基本属性、业务属性、营业时间、标签属性、类目信息、品牌信息及扩展属性。
**内容展示**：选择中文信息展示，除门店ID外，不展示其余id相关内容，例如展示类目名称，非类目id

---

## 调用流程

### Python 脚本调用：

使用封装好的 Python 脚本进行 HTTP 接口调用：

**脚本路径：**

```
script/napos/tool.py
```

**调用方式：**

```bash
python script/napos/tool.py --account-id <门店ID> --sk <鉴权码> --tool-code <工具码>
```

**参数说明：**

| 参数           | 简写 | 类型   | 含义             | 必须 |
| -------------- | ---- | ------ | ---------------- | ---- |
| --account-id   | -a   | string | 餐饮门店ID       | 是   |
| --tool-code    | -t   | string | 工具码           | 是   |
| --sk           | -s   | string | 用户鉴权码       | 是   |
| --raw          | -r   | flag   | 输出原始流式响应 | 否   |
| --output       | -o   | string | 输出文件路径     | 否   |

**调用示例：**

```bash
# 基本调用
python script/napos/tool.py --account-id 528860314 --sk abc123 --tool-code shopinfo

# 保存结果到文件
python script/napos/tool.py --account-id 528860314 --sk abc123 --tool-code shopinfo --output shop_info.md
```

**脚本功能：**

- 自动构建 HTTP 请求体和请求头
- 发起请求时在 header 中携带 `sk` 字段，值为上下文中的用户鉴权码
- 处理流式 SSE 响应
- 解析并返回结构化门店信息
- 支持错误处理和超时控制

---

**展示要求**：

1. 先展示门店核心信息（门店ID、门店名称、经营状态等）
2. 基础属性、业务属性、类目信息、品牌信息分区块展示，层次分明
3. 完整门店信息放在折叠区域，按需展开查看
4. 数据引用保留原始值，不做二次加工
5. 仅展示接口返回的数据，无需额外分析处理

---

## 数据结构说明

接口返回的门店信息数据结构如下：

### ShopInfoDTO

| 字段名            | 类型                     | 说明           |
| ----------------- | ------------------------ | -------------- |
| shopId            | Long                     | 门店ID         |
| shopBaseInfo      | ShopBaseInfoDTO          | 门店基本属性   |
| shopBusinessInfo  | ShopBusinessInfoDTO      | 门店业务属性   |
| shopAttributeMap  | Map<String, String>      | 门店标签属性   |
| shopFlavorInfos   | List<ShopFlavorInfoDTO>  | 门店类目信息   |
| shopBrandDTO      | ShopBrandInfoDTO         | 门店品牌信息   |
| shopExtInfoDTO    | ShopExtInfoDTO           | 门店扩展属性   |

### ShopBaseInfoDTO

门店基本属性

| 字段名          | 类型                  | 说明                                                         |
| --------------- | --------------------- | ------------------------------------------------------------ |
| openId          | String                | 开放平台店铺id                                               |
| shopOid         | Long                  | 店铺oid                                                      |
| shopId          | Long                  | 店铺id                                                       |
| shopStatus      | Integer               | 店铺状态:1-有效,0-无效                |
| shopType        | Integer               | 店铺类型:0-普通店铺,100-测试店铺|
| domId           | Long                  | 商机id                                                       |
| mainShopName    | String                | 总店名                                                       |
| branchShopName  | String                | 分店名                                                       |
| fullShopName    | String                | 总店-分店店铺全名                                            |
| brandId         | Long                  | 店铺所属品牌的id                                             |
| latitude        | BigDecimal            | 纬度                                                         |
| longitude       | BigDecimal            | 经度                                                         |
| provinceId      | Integer               | 省code                                                       |
| cityId          | Integer               | 市code                                                       |
| districtId      | Integer               | 区code                                                       |
| address         | String                | 详细地址                                                     |
| contacts        | List<ShopContactDTO>  | 联系方式                                                     |
| photos          | List<ShopPhotoDTO>    | 店铺的图片                                                   |
| createdAt       | LocalDateTime         | 店铺创建时间                                                 |

### ShopBusinessInfoDTO

门店业务属性

| 字段名                 | 类型                  | 说明                                                         |
| ---------------------- | --------------------- | ------------------------------------------------------------ |
| busyLevel              | Integer               | 营业状态:0-营业中,2-已关闭                            |
| description            | String                | 店铺简介                                                     |
| flexibleServingTimeStr | String                | 营业时间设置(数据库直传)                                     |
| flexibleServingTime    | ShopBusinessTimeDTO   | 营业时间设置                                                 |
| currentTimeIsOpenBusiness | Boolean            | 当前时间是否正在营业中                                       |
| servingTime            | List<List<LocalTime>> | 当天营业时间段 HH:mm                                         |
| promotionInfo          | String                | 店铺公告                                                     |
| shopId                 | Long                  | 店铺id                                                       |
| willCloseAt            | Long                  | 延迟关店时间                                                 |
| firstOpenTime          | LocalDateTime         | 首次营业时间                                                 |
| packingFee             | Double                | 餐盒费                                                       |
| inVocation             | Boolean               | 是否歇业中                                                   |

### ShopFlavorInfoDTO

门店类目信息

| 字段名        | 类型    | 说明                       |
| ------------- | ------- | -------------------------- |
| flavorId      | Long    | 类目id                     |
| flavorName    | String  | 类目名称                   |
| type          | String  | 类目类型：MAJOR-主营类目，MINOR-副营类目                   |
| keywords      | String  | 关键词                     |
| rankingWeight | String  | 排序权重                   |
| position      | String  | 位置                       |
| icon          | String  | 图标                       |
| isValid       | Integer | 是否有效                   |
| path          | String  | 路径                       |
| parentId      | Long    | 父类目id                   |

### ShopBrandInfoDTO

门店品牌信息

| 字段名    | 类型   | 说明     |
| --------- | ------ | -------- |
| brandId   | Long   | 品牌id   |
| brandName | String | 品牌名称 |

### ShopExtInfoDTO

门店扩展属性

| 字段名                  | 类型              | 说明                                 |
| ----------------------- | ----------------- | ------------------------------------ |
| effectiveSupplyValue    | Integer           | 有效共计分                           |
| stockEmpty              | Boolean           | 是否库存为空                         |
| invoice                 | Boolean           | 是否支持发票                         |
| invoiceMinAmount        | Double            | 支持发票最小金额                     |
| selfPickPackingFee      | Double            | 新零售自提包装费                     |
| promisedCookingTime     | Integer           | 承诺出餐时间                         |
| bookable                | Boolean           | 是否可预订                           |
| nonBusinessTimeBooking  | Boolean           | 是否支持非营业时间预定               |
| reserveDays             | Integer           | 最晚预订天数                         |
| minReserveDays          | Integer           | 最早预定天数                         |
| foodSafetyInsurance     | Integer           | 食品安全保险                         |
| newRetail               | Boolean           | 是否已迁移新零售门店                 |
| supportFastChargeback   | Boolean           | 是否支持极速退                       |
| supportCarefreeChargeback | Boolean         | 是否支持无忧退                       |
| supportMultiChargeback  | Boolean           | 是否支持多次退                       |
| supportPartOfRefund     | Boolean           | 是否支持部分退款                     |
| auditAvailableTime      | Integer           | 售后商家审核用户退款申请时限         |
| refundAvailableTime     | Integer           | 售后用户发起退款时效                 |
| premium                 | Boolean           | 是否品牌馆                           |
| orderRemark             | Boolean           | 是否添加订单备注                     |
| orderMode               | Integer           | 订单模式                             |
| reserveTime             | List<LocalTime>   | 预定时间                             |
| openIm                  | Boolean           | 是否开启商户、骑手、用户间聊天功能   |
| updateAt                | LocalDateTime     | 店铺更新时间                         |
| bookingTime             | List<LocalTime>   | 支持预定的时间                       |
| csmPaidCancellation     | Double            | 有偿取消赔付比例                     |
| delayOrderCall          | Integer           | 延迟呼单时间                         |
| hasPromisedCookingTime  | Boolean           | 是否设置过出餐时间                   |
| supportOnlineRefund     | Boolean           | 是否支持在线退单                     |

---

## 答疑能力

当用户对门店信息或数据有疑问时，根据以下规则进行解答。

### 字段释义答疑

- **门店基本属性**：门店名称、地址、联系方式、营业时间等基础信息的含义
- **门店业务属性**：经营状态、配送范围、起送价、配送费等业务配置说明
- **门店标签属性**：门店标签的分类及业务含义解读
- **门店类目信息**：门店所属类目、风味标签的层级关系及展示规则
- **门店品牌信息**：品牌归属、品牌等级、品牌权益等品牌相关说明
- **门店扩展属性**：扩展字段的用途及取值范围说明

### 数据答疑

基于接口返回的门店数据回答，涵盖：

- **数据解读**：帮助用户理解各字段数据含义及取值规范
- **状态说明**：解释门店经营状态、审核状态等各状态的含义及流转规则
- **配置建议**：结合门店实际数据，给出合理的配置优化方向
- **异常排查**：针对数据缺失或异常值，提供可能的原因及排查思路
