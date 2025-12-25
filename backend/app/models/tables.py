from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from app.db.base import Base


class ProjectConstructionRecord(Base):
    """现场施工记录主表ORM模型"""
    __tablename__ = "project_construction_record"
    
    org_id = Column(Integer, primary_key=True, default=0, comment="组织ID、或项目id")
    id = Column(Integer, primary_key=True, comment="id")
    weather = Column(String(50), comment="天气")
    temperature = Column(String(50), comment="温度")
    record_time = Column(DateTime, nullable=False, comment="记录时间")
    commit_time = Column(DateTime, comment="提交时间")
    summarize = Column(String, comment="记录文字")
    creator = Column(Integer, nullable=False, default=0, comment="记录创建人，提交人")
    created_at = Column(DateTime, nullable=False, comment="记录创建时间，提交时间")
    reviser = Column(Integer, nullable=False, default=0, comment="记录修改人")
    updated_at = Column(DateTime, nullable=False, comment="记录修改时间")
    is_removed = Column(Boolean, nullable=False, default=False, comment="删除标记")
    version = Column(Integer, nullable=False, comment="记录版本号")
    
    # 关系定义
    details = relationship("ProjectConstructionRecordDetail", back_populates="record")
    procedure_details = relationship("ProjectConstructionRecordProcedureDetail", back_populates="record")
    progress_quantities = relationship("ProjectConstructionRecordProgressQuantity", back_populates="record")


class ProjectConstructionRecordDetail(Base):
    """现场施工记录详情表ORM模型"""
    __tablename__ = "project_construction_record_detail"
    
    org_id = Column(Integer, primary_key=True, default=0, comment="组织ID、或项目id")
    id = Column(Integer, primary_key=True, comment="id")
    project_construction_record_id = Column(Integer, nullable=False, comment="主表id")
    content = Column(String(16383), comment="记录内容")
    ext_content = Column(String, comment="记录内容扩展")
    record_type = Column(String(50), comment="记录类型")
    level = Column(Integer, nullable=False, default=1, comment="层级")
    order_no = Column(Integer, nullable=False, comment="排序号")
    parent_id = Column(Integer, nullable=False, comment="父记录id")
    full_id = Column(String(2000), nullable=False, comment="ID全路径")
    full_id_ex = Column(String(2000), nullable=False, comment="ID全路径")
    creator = Column(Integer, nullable=False, default=0, comment="记录创建人，提交人")
    created_at = Column(DateTime, nullable=False, comment="记录创建时间，提交时间")
    reviser = Column(Integer, nullable=False, default=0, comment="记录修改人")
    updated_at = Column(DateTime, nullable=False, comment="记录修改时间")
    is_removed = Column(Boolean, nullable=False, default=False, comment="删除标记")
    version = Column(Integer, nullable=False, comment="记录版本号")
    project_labor_team_id = Column(Integer, comment="队伍id")
    project_spot_id = Column(Integer, comment="工点id")
    entry_work_id = Column(Integer, comment="分部分项id")
    
    # 关系定义
    record = relationship("ProjectConstructionRecord", back_populates="details",
                         primaryjoin="and_(ProjectConstructionRecord.tenant==ProjectConstructionRecordDetail.tenant, "
                                    "ProjectConstructionRecord.org_id==ProjectConstructionRecordDetail.org_id, "
                                    "ProjectConstructionRecord.id==ProjectConstructionRecordDetail.project_construction_record_id)")


class ProjectConstructionRecordProcedureDetail(Base):
    """施工记录工序记录字段历史详情表ORM模型"""
    __tablename__ = "project_construction_record_procedure_detail"
    
    org_id = Column(Integer, primary_key=True, default=0, comment="组织ID、或项目id")
    id = Column(Integer, primary_key=True, comment="id")
    project_construction_record_id = Column(Integer, nullable=False, comment="施工记录主表id")
    project_construction_record_detail_id = Column(Integer, nullable=False, comment="施工记录id")
    project_spot_id = Column(Integer, nullable=False, comment="工点id")
    project_labor_team_id = Column(Integer, comment="施工队伍id")
    project_part_id = Column(Integer, comment="部位id")
    project_spot_progress_custom_part_id = Column(Integer, comment="自定义部位id")
    progress_item_id = Column(Integer, comment="形象进度项id")
    progress_item_procedure_detail_id = Column(Integer, nullable=False, comment="记录字段id")
    material_id = Column(Integer, comment="材料id")
    value = Column(String(2000), comment="值")
    ext_value = Column(String(2000), comment="扩展值")
    creator = Column(Integer, nullable=False, default=0, comment="记录创建人，提交人")
    created_at = Column(DateTime, nullable=False, comment="记录创建时间，提交时间")
    reviser = Column(Integer, nullable=False, default=0, comment="记录修改人")
    updated_at = Column(DateTime, nullable=False, comment="记录修改时间")
    is_removed = Column(Boolean, nullable=False, default=False, comment="删除标记")
    version = Column(Integer, nullable=False, comment="记录版本号")
    entry_work_id = Column(Integer, comment="分部分项id")
    entry_work_procedure_template_detail_id = Column(Integer, comment="分项工序施工记录模板记录字段id")
    project_spot_entry_work_custom_part_id = Column(Integer, comment="分项自定义部位id")
    standard_construction_method_part_id = Column(Integer, comment="开挖支护工法部位id")
    
    # 关系定义
    record = relationship("ProjectConstructionRecord", back_populates="procedure_details",
                         primaryjoin="and_(ProjectConstructionRecord.tenant==ProjectConstructionRecordProcedureDetail.tenant, "
                                    "ProjectConstructionRecord.org_id==ProjectConstructionRecordProcedureDetail.org_id, "
                                    "ProjectConstructionRecord.id==ProjectConstructionRecordProcedureDetail.project_construction_record_id)")


class ProjectConstructionRecordProgressQuantity(Base):
    """现场施工记录形象量记录表ORM模型"""
    __tablename__ = "project_construction_record_progress_quantity"
    
    org_id = Column(Integer, primary_key=True, default=0, comment="组织ID、或项目id")
    id = Column(Integer, primary_key=True, comment="id")
    project_construction_record_id = Column(Integer, nullable=False, comment="记录id")
    project_construction_record_detail_id = Column(Integer, comment="记录详情id")
    project_unit_work_id = Column(Integer, comment="单位工程id")
    stat_year = Column(Integer, comment="统计年")
    stat_month = Column(Integer, comment="统计月")
    project_spot_id = Column(Integer, nullable=False, comment="工点id")
    project_labor_team_id = Column(Integer, nullable=False, comment="队伍id")
    project_part_id = Column(Integer, comment="部位id")
    progress_item_id = Column(Integer, nullable=False, comment="形象进度项id")
    progress_item_procedure_id = Column(Integer, comment="工序id")
    progress_item_procedure_detail_id = Column(Integer, comment="详情id")
    construction_location = Column(String(2000), comment="施工位置")
    start_pile = Column(String(255), comment="开始桩号")
    end_pile = Column(String(255), comment="结束桩号")
    quantity = Column(DECIMAL(18, 6), default=0, comment="本次完成形象量")
    stat_quantity = Column(DECIMAL(18, 6), default=0, comment="本次完成统计量")
    amount = Column(DECIMAL(18, 2), default=0, comment="本次完成产值")
    start_time = Column(DateTime, comment="开始时间")
    end_time = Column(DateTime, comment="完成时间")
    complete_percent = Column(DECIMAL(18, 2), comment="本次完成占比")
    design_amount = Column(DECIMAL(18, 2))
    stated_amount = Column(DECIMAL(18, 2))
    stating_amount = Column(DECIMAL(18, 2))
    adjusted_amount = Column(DECIMAL(18, 2))
    status = Column(String(50), default="todo", comment="完成状态")
    progress_quantity_type = Column(String(50), comment="形象量类型")
    creator = Column(Integer, nullable=False, default=0, comment="记录创建人")
    created_at = Column(DateTime, nullable=False, comment="记录创建时间")
    reviser = Column(Integer, nullable=False, default=0, comment="记录修改人")
    updated_at = Column(DateTime, nullable=False, comment="记录修改时间")
    version = Column(Integer, nullable=False, comment="记录版本号")
    is_removed = Column(Boolean, nullable=False, default=False, comment="删除标记")
    design_quantity = Column(DECIMAL(18, 6), comment="形象量设计量")
    design_stat_quantity = Column(DECIMAL(18, 6), comment="统计量设计量")
    entry_work_id = Column(Integer, comment="分部分项id")
    entry_work_property_id = Column(Integer, comment="部位按属性细分后的属性id")
    entry_work_property_value = Column(String(50), comment="部位按属性细分后的属性值")
    project_spot_progress_custom_part_id = Column(Integer, comment="自定义或拆分的部位id")
    entry_work_procedure_id = Column(Integer, comment="分项工序id")
    standard_construction_method_part_id = Column(Integer, comment="开挖支护工法部位id")
    project_spot_entry_work_custom_part_id = Column(Integer, comment="分项自定义部位id")
    expired_status = Column(String(50), comment="作废状态")
    project_divisional_work_id = Column(Integer, comment="工程实体分项id")
    procedure_percent = Column(DECIMAL(5, 2), comment="工序完成比例")
    divided_part_percent = Column(DECIMAL(5, 2), comment="拆分部位所占比例")
    pile_no_prefix = Column(String(50), comment="桩号前缀")
    start_pile_no = Column(DECIMAL(18, 6), comment="开始桩号")
    end_pile_no = Column(DECIMAL(16, 6), comment="结束桩号")
    side = Column(String(50), comment="路面分项的幅别")
    
    # 关系定义
    record = relationship("ProjectConstructionRecord", back_populates="progress_quantities",
                         primaryjoin="and_(ProjectConstructionRecord.tenant==ProjectConstructionRecordProgressQuantity.tenant, "
                                    "ProjectConstructionRecord.org_id==ProjectConstructionRecordProgressQuantity.org_id, "
                                    "ProjectConstructionRecord.id==ProjectConstructionRecordProgressQuantity.project_construction_record_id)")