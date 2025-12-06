# Camera Platform - Complete Shopping List

## Hardware Components

### Core System (Already Ordered - Arriving Today)
| Item | Quantity | Status |
|------|----------|--------|
| Raspberry Pi 5 (8GB) with Active Cooler | 1 | ✅ Ordered |
| Arducam OwlSight 64MP Camera | 1 | ✅ Ordered |
| GeeekPi AI HAT+ (Hailo-8, 26 TOPS) | 1 | ✅ Ordered |
| PWM Servo Driver HAT (16-channel) | 1 | ✅ Ordered |
| Stewart Platform with 6× 80KG Servos | 1 | ✅ Ordered |

---

## Additional Components Needed

### 1. G-Force Sensor
| Item | Specs | Cost | Link |
|------|-------|------|------|
| **Adafruit ADXL345 Triple-Axis Accelerometer** | ±2/4/8/16g, I2C/SPI, 13-bit | $14.95 | [Adafruit #1231](https://www.adafruit.com/product/1231) |

**Why this sensor:**
- Industry-standard, proven reliability
- Open-source, non-proprietary
- Perfect range (±8g) for camera platform
- Excellent documentation and support
- Low power consumption (40µA)
- High resolution (13-bit, 4mg/LSB)

**Alternatives (if out of stock):**
- SparkFun ADXL345: [SparkFun SEN-09836](https://www.sparkfun.com/products/9836)
- Generic ADXL345 breakout: Amazon/eBay (~$5-10)

---

### 2. Power System

#### UPS Power Supply (for Computing)
| Option | Specs | Cost | Link |
|--------|-------|------|------|
| **Recommended:** Adafruit PowerBoost 1000C | 5V 2A, LiPo charger | $19.95 | [Adafruit #2465](https://www.adafruit.com/product/2465) |
| **Alternative:** Anker PowerCore 10000 | 5V 2.4A USB | $25-35 | Amazon |
| **Budget:** Generic USB Power Bank | 5V 2A+ | $15-25 | Amazon |

**Plus LiPo Battery (for PowerBoost):**
| Item | Specs | Cost | Link |
|------|-------|------|------|
| 3.7V 2500mAh LiPo | JST connector | $14.95 | [Adafruit #328](https://www.adafruit.com/product/328) |
| 3.7V 6600mAh LiPo | Longer runtime | $29.95 | [Adafruit #353](https://www.adafruit.com/product/353) |

#### Servo Battery Pack
| Option | Specs | Cost | Link |
|--------|-------|------|------|
| **Recommended:** 2S LiPo (7.4V) | 5000mAh, 30C | $30-40 | HobbyKing, Amazon |
| **Alternative:** 6V NiMH | 5000mAh | $25-35 | Amazon |
| **Budget:** 6× AA Battery Holder | With rechargeable AAs | $15-20 | Amazon |

**Important:** Servos need high current capacity (15A peak)

#### Battery Charger
| Option | Type | Cost | Link |
|--------|------|------|------|
| **For LiPo:** SkyRC iMAX B6 | Balance charger | $25-35 | Amazon, HobbyKing |
| **For NiMH:** Tenergy Smart Charger | Universal | $20-30 | Amazon |

---

### 3. Cables & Connectors

| Item | Quantity | Cost | Notes |
|------|----------|------|-------|
| **Jumper Wires** (M-F, 20cm) | 40-pack | $5-8 | For sensor connections |
| **JST Connectors** | 5-pack | $5-10 | For battery connections |
| **XT60 Connectors** | 5-pack | $8-12 | For high-current servo power |
| **USB-C Cable** (1m) | 1 | $8-12 | For Raspberry Pi power |
| **Servo Extension Cables** (30cm) | 6 | $10-15 | If servos too far from HAT |

---

### 4. Mounting Hardware

| Item | Quantity | Cost | Notes |
|------|----------|------|-------|
| **M2.5 Screws & Standoffs Kit** | 1 set | $10-15 | For ADXL345 mounting |
| **Double-Sided Foam Tape** | 1 roll | $5-8 | Alternative mounting |
| **Velcro Straps** | 5-pack | $8-12 | Cable management |
| **Heat Shrink Tubing** | Assorted | $8-12 | Wire protection |

---

### 5. Optional but Recommended

| Item | Purpose | Cost | Link |
|------|---------|------|------|
| **MicroSD Card** (64GB+, Class 10) | OS and data storage | $12-20 | Amazon |
| **SD Card Reader** | For flashing OS | $8-12 | Amazon |
| **HDMI Cable** | Initial setup | $8-12 | Amazon |
| **USB Keyboard/Mouse** | Initial setup | $15-25 | Amazon |
| **Multimeter** | Voltage/current testing | $15-25 | Amazon |
| **Soldering Kit** | For permanent connections | $25-40 | Amazon |
| **Wire Stripper** | Cable preparation | $10-15 | Amazon |
| **Small Screwdriver Set** | Assembly | $10-15 | Amazon |

---

## Cost Summary

### Minimum Required (Already Have Core System)
| Category | Cost |
|----------|------|
| ADXL345 Sensor | $15 |
| UPS Power (PowerBoost + Battery) | $35 |
| Servo Battery Pack | $30 |
| Battery Charger | $25 |
| Cables & Connectors | $30 |
| Mounting Hardware | $15 |
| **Subtotal** | **$150** |

### Recommended (with Optional Items)
| Category | Cost |
|----------|------|
| Minimum Required | $150 |
| MicroSD Card | $15 |
| Tools & Accessories | $50 |
| **Total** | **$215** |

### Budget Option (Minimal)
| Category | Cost |
|----------|------|
| ADXL345 Sensor | $15 |
| USB Power Bank | $20 |
| 6× AA Battery Holder + Batteries | $20 |
| Basic Cables | $15 |
| Foam Tape | $5 |
| **Total** | **$75** |

---

## Where to Buy

### Electronics Components
1. **Adafruit** - https://www.adafruit.com
   - ADXL345 sensor
   - PowerBoost modules
   - LiPo batteries
   - Quality components, excellent support

2. **SparkFun** - https://www.sparkfun.com
   - Alternative ADXL345
   - Development tools
   - Educational resources

3. **Amazon** - https://www.amazon.com
   - Fast shipping
   - Wide selection
   - Competitive prices
   - Good for cables, tools, batteries

4. **DigiKey** - https://www.digikey.com
   - Professional components
   - Bulk pricing
   - Technical datasheets

### Hobby/RC Components
1. **HobbyKing** - https://www.hobbyking.com
   - LiPo batteries
   - Battery chargers
   - RC connectors
   - Best prices for batteries

2. **Amazon** - RC section
   - Quick shipping
   - Good selection
   - Customer reviews

### Local Options
- **Micro Center** - Electronics, Raspberry Pi
- **Fry's Electronics** - Components, tools
- **Local hobby shops** - RC batteries, chargers
- **Hardware stores** - Mounting hardware, tools

---

## Purchasing Priority

### Order Immediately (Critical Path)
1. ✅ **Adafruit ADXL345** - Core sensor, may have shipping delay
2. ✅ **Power supplies** - Need for testing
3. ✅ **Cables & connectors** - Can't test without them

### Order Soon (Week 1)
4. **MicroSD card** - If not already have
5. **Basic tools** - If not already have
6. **Mounting hardware** - For final assembly

### Order Later (Week 2-3)
7. **Optional accessories** - As needed
8. **Spare parts** - After testing
9. **Upgrades** - Based on experience

---

## Shipping Considerations

### Adafruit
- **Shipping:** $5-10 (USPS)
- **Time:** 3-7 days
- **Tip:** Combine orders to save on shipping

### Amazon
- **Prime:** Free 2-day shipping
- **Standard:** 5-7 days
- **Tip:** Check "Ships from Amazon" for faster delivery

### HobbyKing
- **International:** 2-4 weeks
- **US Warehouse:** 3-7 days
- **Tip:** Check warehouse location before ordering

---

## Money-Saving Tips

1. **Bundle Orders**
   - Combine Adafruit items in one order
   - Use Amazon Subscribe & Save for batteries
   - Check for free shipping thresholds

2. **Check for Alternatives**
   - Generic ADXL345 breakouts (~$5 vs $15)
   - USB power banks instead of custom UPS
   - Rechargeable AA batteries instead of LiPo

3. **Use What You Have**
   - Old phone charger for 5V power
   - Existing USB cables
   - Spare microSD cards
   - Tools you already own

4. **Wait for Sales**
   - Adafruit has occasional sales
   - Amazon Prime Day / Black Friday
   - HobbyKing clearance section

5. **Buy Generic When Possible**
   - Cables and connectors
   - Mounting hardware
   - Basic tools
   - **But not:** Sensors, power supplies (quality matters!)

---

## Quality vs. Cost Trade-offs

### Worth Paying More For:
✅ **ADXL345 from Adafruit** - Reliable, documented, supported
✅ **Quality LiPo batteries** - Safety and performance
✅ **Good battery charger** - Protects investment
✅ **Proper connectors** - Reliability and safety

### Can Go Budget:
✅ **Jumper wires** - Generic is fine
✅ **Mounting hardware** - Standard screws work
✅ **Cable management** - Zip ties vs. velcro
✅ **Tools** - Basic set is sufficient

### Don't Cheap Out On:
❌ **Power supplies** - Fire hazard if poor quality
❌ **LiPo charger** - Safety critical
❌ **Sensors** - Accuracy matters
❌ **Servo power** - Insufficient current = damage

---

## Checklist

### Before Ordering
- [ ] Verify core system is ordered/arriving
- [ ] Check what tools/supplies you already have
- [ ] Confirm shipping addresses
- [ ] Check for coupon codes
- [ ] Compare prices across vendors

### After Ordering
- [ ] Track shipments
- [ ] Prepare workspace
- [ ] Review documentation
- [ ] Plan assembly sequence
- [ ] Prepare for testing

### Upon Arrival
- [ ] Inspect all items
- [ ] Test components individually
- [ ] Organize by assembly phase
- [ ] Keep packaging for returns
- [ ] Document any issues

---

## Return Policy Notes

### Adafruit
- 30-day return policy
- Must be unused/undamaged
- Restocking fee may apply
- Keep original packaging

### Amazon
- 30-day return window
- Free returns on most items
- Easy return process
- Keep boxes for returns

### HobbyKing
- 7-day return policy
- International returns difficult
- Check items immediately
- Document any damage

---

**Last Updated:** 2024  
**Total Estimated Cost:** $150-215 (beyond core system)  
**Budget Option:** $75 minimum  
**Recommended:** $150-180 for quality components